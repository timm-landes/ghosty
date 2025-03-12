"""
TCP/IP communication interface for the GHOST spectrometer software.

This module handles the low-level communication with the GHOST software
using a TCP/IP connection. It implements the command protocol and provides
methods for sending commands and receiving responses.
"""

import telnetlib
from loguru import logger
import time
import asyncio  # Add this import

class TcpIpController:
    """TCP/IP controller for GHOST software communication.
    
    Handles the TCP/IP connection to the GHOST software and implements
    the command protocol. Commands are sent as ASCII strings and responses
    are read until a termination condition is met.
    
    Args:
        host (str): IP address of the GHOST software
        port (int): TCP port number for the connection
    """
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        self.connection = telnetlib.Telnet(self.host, self.port)

    def send_command(self, command):
        if self.connection is None:
            raise ValueError("Connection not established. Call connect() first.")
            
        if len(command) > 80:
            raise ValueError(f"Command too long ({len(command)} chars). GHOST commands must be 80 characters or less.")

        self.connection.write(command.encode('utf-8') + b'\r\n')
        response = ""
        while True:
            line = self.connection.read_until(b'\r\n', timeout=5).decode('utf-8')
            response += line
            if command == 'STATUS' and 'END OF REPORT' in line:
                break
            elif not line or line.strip() == '':
                break
                    
        return response.strip()

    def send_command_no_response(self, command):
        """Send command without waiting for response"""
        if self.connection is None:
            raise ValueError("Connection not established. Call connect() first.")
            
        if len(command) > 80:
            raise ValueError(f"Command too long ({len(command)} chars). GHOST commands must be 80 characters or less.")

        self.connection.write(command.encode('utf-8') + b'\r\n')
        logger.debug(f"Command (no response): {command}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def chat(self, text):
        return self.send_command(f'CHAT "{text}"')

    def ghost(self, text):
        if len(text) > 80:
            raise ValueError("GHOST command text can be up to 80 characters.")
        return self.send_command(f'GHOST {text}')

    def data(self):
        return self.send_command('DATA')

    def delete(self):
        return self.send_command_no_response('DELETE')

    def get_realtime(self):
        return self.send_command('GET_REALTIME')

    def get_shutter(self):
        return self.send_command('GET_SHUTTER')

    def help(self):
        return self.send_command('HELP')

    def status(self):
        return self.send_command('STATUS')

    def observe(self):
        return self.send_command_no_response('OBSERVE')

    def override(self):
        return self.send_command('OVERRIDE')

    def save(self, name):
        return self.send_command_no_response(f'SAVE {name}')

    def saveraw(self, name):
        return self.send_command(f'SAVERAW {name}')

    def set_show_current(self):
        return self.send_command('SET SHOW_CURRENT')

    def set_channels(self, num_channels):
        return self.send_command(f'SET{num_channels}')

    def start(self, cycles):
        return self.send_command_no_response(f'START {cycles}')

    def stop(self):
        return self.send_command_no_response('STOP')

    def text(self):
        return self.send_command('TEXT')

    def restore(self):
        return self.send_command('RESTORE')

    def set_working_directory(self, directory):
        return self.send_command_no_response(f'WDIR {directory}')

    def get_working_directory(self):
        return self.send_command('WDIR')

    async def is_acquiring(self, max_retries=4):
        """Check if the system is currently acquiring data.
        
        Sends a STATUS command and parses the response to determine if
        the system is in IDLE or ACQUIRING state.
        
        Args:
            max_retries (int): Number of retry attempts if status check fails
            
        Returns:
            bool: True if system is acquiring, False if idle
            
        Note:
            Returns True if status cannot be determined to prevent premature
            progression in the acquisition sequence.
        """
        
        for attempt in range(max_retries):
            response = self.send_command('STATUS')
            lines = response.split('\n')
            
            for line in lines[:5]:
                line = line.strip()
                if 'GHOST STATUS REPORT' in line:
                    is_idle = 'IDLE' in line
                    logger.trace(f"Status line: {line}")
                    return not is_idle  # Return True if NOT idle (i.e., acquiring)
            
            if attempt < max_retries - 1:
                logger.debug(f"Status not found, retrying ({attempt + 1}/{max_retries})")
                await asyncio.sleep(0.05)
            
        logger.error("Could not get valid status response")
        return True  # Safer to assume still acquiring if status unclear
    
    async def test_spectrometer(self):
        """Test if spectrometer is physically connected.
        
        Returns:
            bool: True if no error, False if connection error
        """
        response = self.send_command('OBSERVE')
        return "Error : server cannot open serial port" not in response
        await asyncio.sleep(0.1)  # Add this line
        self.stop()