"""
Interface for controlling the GHOST Brillouin spectrometer.

This module provides a high-level interface for controlling the GHOST spectrometer
software, handling acquisition timing, and managing the communication protocol.

The module implements timing calculations based on the spectrometer's clock frequency:
- Standard mode: 4 kHz clock (~615 ms per scan+retract cycle)
- High-speed mode: 10 kHz clock (~250 ms per scan+retract cycle, requires hardware mods)

Key Features:
- Automatic timing calculations based on clock frequency
- Robust acquisition with timeout handling
- Status polling with configurable retry logic
- Acquisition timing logging
- Working directory management
- Error handling and recovery
"""

import asyncio 
from .ghost_communication import TcpIpController
from .timing_logger import TimingLogger
from loguru import logger
import time
import os
import random

class BrillouinSpectrometer:
    """Controller interface for the GHOST spectrometer software.
    
    This class manages the connection to the GHOST software and provides methods
    for data acquisition and control. It handles timing based on the spectrometer's
    clock frequency and manages the TCP/IP communication.
    
    The spectrometer can operate in two modes:
    1. Standard mode (4 kHz): Uses full 2048 MCA channels
       - Scan time: ~512 ms
       - Total cycle time: ~615 ms (scan + retract)
       
    2. High-speed mode (10 kHz): Uses 512 MCA channels
       - Scan time: ~205 ms
       - Total cycle time: ~250 ms (scan + retract)
       - Requires hardware modifications
    
    Args:
        clock_frequency_khz (int): Clock frequency in kHz (default: 4).
    
    Attributes:
        cycle_time_ms (float): Calculated time per measurement cycle
        min_wait_ratio (float): Minimum wait time as ratio of theoretical time
        timeout_margin_ms (float): Additional margin for timeouts
        has_control (bool): Whether this instance has control of the spectrometer
        _initialized (bool): Whether the connection is initialized
    
    Note:
        Always use async with context manager or call close() when done
    """
    def __init__(self, clock_frequency_khz=4):
        self._ghost = None
        self._initialized = False
        self.has_control = False
        self.timing_logger = None
        
        # Calculate timing constants based on clock frequency
        self.clock_frequency = clock_frequency_khz * 1000  # Convert to Hz
        # Base acquisition time per cycle (ms) = 2460 clock cycles / frequency
        self.cycle_time_ms = (2460 / self.clock_frequency) * 1000
        
        # Safety margins for timeouts
        self.min_wait_ratio = 0.6  # Wait at least 60% of theoretical time
        self.timeout_margin_ms = self.cycle_time_ms * 10  # Add 10 cycles as margin
        
        logger.info(f"Initialized with {clock_frequency_khz}kHz clock")
        logger.info(f"Calculated cycle time (scan = retract): {self.cycle_time_ms:.2f}ms")

    async def initialize(self):
        """Initialize the spectrometer software connection"""
        try:
            self._ghost = TcpIpController('127.0.0.1', 4000)
            self._ghost.connect()
            await asyncio.sleep(3)  # Wait for connection and welcome
            
            # Take control and verify
            self._ghost.override()
            self.has_control = True
            await asyncio.sleep(0.1)  # Wait for control to take effect

            # Test physical spectrometer connection
            if not await self.test_spectrometer_connection():
                raise RuntimeError("No spectrometer connected - Check connection network server state")
            
            await asyncio.sleep(0.5)  # Wait for control to take effect
            self._ghost.stop()  # Stop any ongoing acquisition
            await asyncio.sleep(0.1)  # Wait for stop to take effect
            self._ghost.delete() # Delete any existing data
            self._initialized = True
            logger.info("Connection to GHOST software established")
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error initializing spectrometer: {e}")
            raise

    async def close(self):
        """Close the spectrometer connection"""     
        try:
            if self._ghost is not None:
                if self.has_control:
                    self._ghost.restore()
                    self.has_control = False
                self._ghost.close()
                self._initialized = False
        except Exception as e:
            logger.error(f"Error closing spectrometer connection: {e}")
            raise

    async def set_working_directory(self, directory):
        """Set the working directory for GHOST software"""
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        if not self.has_control:
            raise Exception("No remote control")
        try:
            self._ghost.set_working_directory(directory)
            # Initialize timing logger in data directory
            self.timing_logger = TimingLogger(directory)
            logger.debug(f"Working directory set to: {directory}")
        except Exception as e:
            logger.error(f"Error setting working directory: {e}")
            raise

    async def wait_for_TFP(self, timeout=None, cycles=1):
        """Wait for the TFP to finish acquisition"""
        start_time = time.perf_counter()
        min_wait = (cycles * self.cycle_time_ms / 1000) * self.min_wait_ratio
        required_idle_count = 2
        idle_count = 0
        
        # Always wait for minimum time before checking status
        while (time.perf_counter() - start_time) < min_wait:
            await asyncio.sleep(0.05)
            
        # Then start checking status
        while True:
            if timeout is not None and (time.perf_counter() - start_time) > timeout:
                logger.warning("Timeout waiting for TFP acquisition")
                return False
                
            if not await self.is_acquiring():
                idle_count += 1
                if idle_count >= required_idle_count:
                    logger.debug(f"Got {required_idle_count} consecutive IDLE states")
                    return True
            else:
                idle_count = 0  # Reset counter if we see any ACQUIRING state
                
            await asyncio.sleep(0.05)  # Poll every 60ms # TODO: Adjust polling interval

    async def acquire_and_save(self, cycles: int, fname: str) -> None:
        """Acquire Brillouin data and save to file.
        
        Performs a complete acquisition cycle:
        1. Deletes any previous data in buffer
        2. Starts new acquisition for specified cycles
        3. Waits for completion with timeout protection
        4. Saves data to specified file
        
        The acquisition timing follows these rules:
        - Minimum wait time: 60% of theoretical acquisition time
        - Timeout: theoretical time + 10 cycle margin
        - Requires 2 consecutive IDLE states to confirm completion
        
        Args:
            cycles: Number of measurement cycles to perform
            fname: Filename to save the data (without path)
            
        Raises:
            TimeoutError: If acquisition exceeds timeout
            Exception: For initialization or control errors
            
        Note:
            Acquisition time is logged if timing_logger is configured
        """
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        if not self.has_control:
            raise Exception("No remote control")
        try:
            start_time = time.perf_counter()
            
            # Delete previous data if any
            self._ghost.delete()
            
            await asyncio.sleep(0.05)
            
            # Start acquisition
            t0 = time.perf_counter()
            self._ghost.start(cycles)
            
            await asyncio.sleep(0.02)
            # Wait for acquisition using status polling
            theoretical_time = cycles * self.cycle_time_ms / 1000  # Convert to seconds
            timeout = theoretical_time + (self.timeout_margin_ms / 1000)
            success = await self.wait_for_TFP(timeout, cycles)
            if not success:
                raise TimeoutError("TFP acquisition timeout")
            
            # Save data
            self._ghost.save(fname)
            t1 = time.perf_counter()
            acquisition_time = (t1-t0)*1000
            logger.debug(f"Acquisition took {acquisition_time:.1f}ms")
            
            
            # Log timings to CSV
            if self.timing_logger:
                self.timing_logger.log_timing(
                    fname, cycles, acquisition_time
                )
            
        except Exception as e:
            logger.error(f"Error acquiring data: {e}")
            raise

    async def get_realtime_data(self):
        """Get real-time data from the spectrometer"""
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        try:
            data = self._ghost.get_realtime()
            if "Error" in data:
                raise RuntimeError(f"Failed to get data: {data}")
            return data
        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            raise

    async def is_acquiring(self, max_retries=4):
        """Check if the system is currently acquiring data.
        
        Sends STATUS commands and parses responses to determine system state.
        Uses multiple retries to handle potential communication issues.
        
        Args:
            max_retries (int): Maximum number of STATUS command attempts
            
        Returns:
            bool: True if system is acquiring, False if IDLE
            
        Note:
            Returns True if status cannot be determined to prevent premature
            progression in acquisition sequences
        """
        for attempt in range(max_retries):
            response = self._ghost.send_command('STATUS')
            lines = response.split('\n')
            
            for line in lines[:5]:
                line = line.strip()
                if 'GHOST STATUS REPORT' in line:
                    is_idle = 'IDLE' in line
                    logger.trace(f"Status line: {line}")
                    return not is_idle  # Return True if not idle (i.e., acquiring)
            
            if attempt < max_retries - 1:
                logger.debug(f"Status not found, retrying ({attempt + 1}/{max_retries})")
                await asyncio.sleep(0.05)
            
        logger.error("Could not get valid status response")
        return True  # Safer to assume still acquiring if status unclear

    async def test_spectrometer_connection(self):
        """Test if spectrometer is physically connected.
        
        Returns:
            bool: True if no error, False if connection error
        """
        response = self._ghost.send_command('OBSERVE')
        await asyncio.sleep(0.1)
        self._ghost.stop()
        return "Error : server cannot open serial port" not in response

    async def get_system_info(self):
        """Get system information from the GHOST software.
        
        Returns:
            dict: System information including version and hardware details
        """
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        try:
            response = self._ghost.send_command('INFO')
            return self._parse_info_response(response)
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise

    async def set_channels(self, num_channels):
        """Set the number of MCA channels.
        
        Args:
            num_channels (int): Number of channels (256 or 512 or 1024)
        """
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        if num_channels not in [256, 512, 1024]:
            raise ValueError("Number of channels must be 256 or 512 or 1025")
        try:
            self._ghost.set_channels(num_channels)
            logger.debug(f"Set channels to {num_channels}")
        except Exception as e:
            logger.error(f"Error setting channels: {e}")
            raise

    async def get_raw_data(self, filename: str):
        """Save raw scan data to file.
        
        Args:
            filename (str): Name for the raw data file
        """
        if not self._initialized:
            raise Exception("Spectrometer not initialized")
        try:
            self._ghost.saveraw(filename)
            logger.debug(f"Saved raw data to {filename}")
        except Exception as e:
            logger.error(f"Error saving raw data: {e}")
            raise

    def _parse_info_response(self, response: str) -> dict:
        """Parse the INFO command response into a structured format.
        
        Args:
            response (str): Raw response from INFO command
            
        Returns:
            dict: Parsed system information
        """
        info = {}
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info

# Test section
if __name__ == "__main__":
    import os
    
    async def test_brillouin():
        # Create spectrometer with 10kHz clock
        spec = BrillouinSpectrometer(clock_frequency_khz=4)
        try:
            print("Initializing spectrometer...")
            await spec.initialize()
            
            # Set working directory
            test_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Test_acq2")
            data_dir = os.path.join(test_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            print(f"Setting working directory to: {data_dir}")
            await spec.set_working_directory(data_dir)
            
            # Acquire test data
            
            rnd = random.randint(1, 10)
            print("Acquiring test data...")
            await spec.acquire_and_save(rnd, "test_spectrum.DAT")
            
            # # Get realtime data
            # print("Getting realtime data...")
            # data = await spec.get_realtime_data()
            # print(f"Received data: {data}")
            
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            print("Closing spectrometer...")
            await spec.close()
            
    # Run the test
    try:
        asyncio.run(test_brillouin())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")


