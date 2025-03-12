# ghosty

A Python wrapper for the Table Stable Ltd. Ghost Software for controlling the TFP-1, and the TFP-2 HC Brillouin spectrometer.

## Installation

Since this package is not yet available on PyPI, you can install it directly from GitLab vis SSH:

```bash
git clone git@gitlab.uni-hannover.de:phytophotonics/ghosty.git
cd ghostpy
pip install -e .
```

### Prerequisites

- Python >=3.6, <=3.12
- Git
- GHOST software installed and running
- TCP/IP connection to GHOST software (default: localhost:4000)

### Development Installation

For development, install with additional dependencies:

```bash
git clone git@gitlab.uni-hannover.de:phytophotonics/ghosty.git
cd ghostpy
pip install -e ".[dev]"
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

## License
MIT License