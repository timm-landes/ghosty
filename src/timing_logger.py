"""
Logging utility for GHOST spectrometer timing measurements.

This module provides functionality for logging timing information during
spectrometer operation. It creates timestamped CSV files containing
acquisition timings for performance analysis.
"""

import os
import csv
from datetime import datetime

class TimingLogger:
    """Logger for spectrometer timing measurements.
    
    Creates and manages CSV log files containing timing information for
    spectrometer operations. Each session creates a new timestamped file.
    
    Args:
        base_dir (str): Base directory for storing log files
            
    Attributes:
        log_dir (str): Directory containing the timing log files
        log_file (str): Path to the current log file
    """
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.log_dir = os.path.join(base_dir, 'timing_logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create new log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(self.log_dir, f'timing_log_{timestamp}.csv')
        
        # Create CSV with headers if new file
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Filename', 'Cycles', 
                               'Acquisition_ms'])

    def log_timing(self, filename: str, cycles: int, acquisition_ms: float):
        """Log timing information to CSV file.
        
        Args:
            filename: Name of the data file being saved
            cycles: Number of measurement cycles
            acquisition_ms: Total acquisition time in milliseconds
        """
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                filename,
                cycles,
                f"{acquisition_ms:.1f}"
            ])
