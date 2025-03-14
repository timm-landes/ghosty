"""
TCP/IP communication interface for the GHOST spectrometer software.

This module handles the low-level communication with the GHOST software
using a TCP/IP connection. It implements the command protocol and provides
methods for sending commands and receiving responses.

The GHOST software uses a simple ASCII-based protocol over TCP/IP where:
- Commands are sent as ASCII strings terminated by CR+LF
- Maximum command length is 80 characters
- Responses are terminated by empty line or specific markers
- Some commands expect responses, others don't

Protocol Details:
- Port: 4000 (default)
- Encoding: UTF-8
- Termination: \r\n (CR+LF)
- Timeout: 5 seconds (default)
"""

import telnetlib # requires python<=3.12.9, otherwise install telnetlib3
from loguru import logger

class TcpIpController:
    """TCP/IP controller for GHOST software communication.
    
    Handles the TCP/IP connection to the GHOST software and implements
    the command protocol. Commands are sent as ASCII strings and responses
    are read until a termination condition is met.
    
    The controller supports two types of commands:
    1. Commands that expect a response (send_command)
    2. Commands without response (send_command_no_response)
    
    Args:
        host (str): IP address of the GHOST software
        port (int): TCP port number for the connection
        
    Attributes:
        host (str): Stored host address
        port (int): Stored port number
        connection (telnetlib.Telnet): Active telnet connection or None
        
    Note:
        Always call connect() before sending commands
        Always call close() when done to release resources
    """
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """Establish TCP/IP connection to the GHOST software.
        
        Raises:
            ConnectionRefusedError: If connection cannot be established
            TimeoutError: If connection times out
        """
        self.connection = telnetlib.Telnet(self.host, self.port)

    def send_command(self, command):
        """Send a command and wait for response.
        
        Sends an ASCII command to the GHOST software and waits for the complete
        response. The response is read until an empty line or specific termination
        marker is encountered.
        
        Args:
            command (str): Command string to send (max 80 chars)
            
        Returns:
            str: Response from the GHOST software with whitespace stripped
            
        Raises:
            ValueError: If connection not established or command too long
            TimeoutError: If response not received within timeout
        """
        if self.connection is None:
            raise ValueError("Connection not established. Call connect() first.")
            
        if len(command) > 80:
            raise ValueError(f"Command too long ({len(command)} chars). GHOST commands must be 80 characters or less.")
    
        logger.debug(f"Command: {command}")
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
        """Send command without waiting for response
        
        Args:
            command (str): Command string to send (max 80 chars)
            
        Raises:
            ValueError: If connection not established or command too long
        """
        if self.connection is None:
            raise ValueError("Connection not established. Call connect() first.")
            
        if len(command) > 80:
            raise ValueError(f"Command too long ({len(command)} chars). GHOST commands must be 80 characters or less.")

        self.connection.write(command.encode('utf-8') + b'\r\n')
        logger.debug(f"Command (no response): {command}")

    def close(self):
        """Close the TCP/IP connection to the GHOST software."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def chat(self, text):
                return self.send_command(f'CHAT "{text}"')



    def delete(self):
        """Send a delete command to the GHOST software without waiting for response."""
        return self.send_command_no_response('DELETE')

    def get_realtime(self):
        """Request real-time data from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('GET_REALTIME')

    def get_shutter(self):
        """Request shutter status from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('GET_SHUTTER')

    def help(self):
        """Request help information from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('HELP')

    def status(self):
        """Request status report from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('STATUS')

    def observe(self):
        """Send an observe command to the GHOST software without waiting for response."""
        return self.send_command_no_response('OBSERVE')

    def override(self):
        """Send an override command to the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('OVERRIDE')

    def save(self, name):
        """Send a save command to the GHOST software without waiting for response.
        
        Args:
            name (str): Name to save the data under
        """
        return self.send_command_no_response(f'SAVE {name}')

    def saveraw(self, name):
        """Send a save raw data command to the GHOST software.
        
        Args:
            name (str): Name to save the raw data under
            
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command(f'SAVERAW {name}')

    def set_show_current(self):
        """Send a command to set the current display mode in the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('SET SHOW_CURRENT')

    def set_channels(self, num_channels):
        """Send a command to set the number of channels in the GHOST software.
        
        Args:
            num_channels (int): Number of channels to set
            
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command(f'SET{num_channels}')

    def start(self, cycles):
        """Send a start command to the GHOST software without waiting for response.
        
        Args:
            cycles (int): Number of cycles to start
        """
        return self.send_command_no_response(f'START {cycles}')

    def stop(self):
        """Send a stop command to the GHOST software without waiting for response."""
        return self.send_command_no_response('STOP')

    def text(self):
        """Request text data from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('TEXT')

    def restore(self):
        """Send a restore command to the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('RESTORE')

    def set_working_directory(self, directory):
        """Send a command to set the working directory in the GHOST software without waiting for response.
        
        Args:
            directory (str): Directory path to set
        """
        return self.send_command_no_response(f'WDIR {directory}')

    def get_working_directory(self):
        """Request the current working directory from the GHOST software.
        
        Returns:
            str: Response from the GHOST software
        """
        return self.send_command('WDIR')