# ghostpy

A Python wrapper for the Table Stable Ltd. Ghost Software for controlling Brillouin spectrometers.

## Installation

```bash
pip install ghostpy
```

## Usage

```python
import asyncio
from ghostpy import BrillouinSpectrometer

async def main():
    # Initialize spectrometer
    spec = BrillouinSpectrometer()
    
    try:
        # Connect to GHOST software
        await spec.initialize()
        
        # Set working directory
        await spec.set_working_directory("path/to/data/dir")
        
        # Acquire and save data
        await spec.acquire_and_save(cycles=10, fname="spectrum.DAT")
        
    finally:
        await spec.close()

asyncio.run(main())
```

## Requirements
- Python >=3.6, <=3.12
- GHOST software installed and running
- TCP/IP connection to GHOST software (default: localhost:4000)

## License
MIT License