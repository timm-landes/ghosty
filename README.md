# Ghosty - GHOST Brillouin Spectrometer Control

Python interface for controlling the GHOST Brillouin spectrometer software via TCP/IP communication.

## Features

- Asynchronous control interface for the GHOST spectrometer
- Automatic timing calculations based on clock frequency
- Robust acquisition with timeout handling and retry logic
- Acquisition timing logging
- Working directory management
- Comprehensive error handling and recovery
- Support for both standard (4 kHz) and high-speed (10 kHz) modes

## Installation

### From Git Repository

1. Clone the repository:
```bash
git clone https://github.com/timm-landes/ghosty.git
cd ghosty
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install in development mode:
```bash
pip install -e .
```

## Quick Start

```python
import asyncio
from ghosty import BrillouinSpectrometer

async def main():
    # Create spectrometer instance (4 kHz standard mode)
    spec = BrillouinSpectrometer(clock_frequency_khz=4)
    
    try:
        # Initialize connection
        await spec.initialize()
        
        # Set working directory
        await spec.set_working_directory("C:/Data")
        
        # Acquire data
        await spec.acquire_and_save(cycles=10, fname="spectrum.DAT")
        
    finally:
        # Clean up
        await spec.close()

asyncio.run(main())
```

## Operating Modes

### Standard Mode (4 kHz)
- Uses full 2048 MCA channels
- Scan time: ~512 ms
- Total cycle time: ~615 ms (scan + retract)

### High-Speed Mode (10 kHz)
- Uses 512 MCA channels
- Scan time: ~205 ms
- Total cycle time: ~250 ms (scan + retract)
- Requires hardware modifications

## Communication Protocol

The GHOST software uses a TCP/IP protocol with the following specifications:

- Port: 4000 (default)
- Encoding: UTF-8
- Command termination: \r\n (CR+LF)
- Maximum command length: 80 characters
- Default timeout: 5 seconds

## Key Components

### BrillouinSpectrometer
High-level interface providing:
- Connection management
- Acquisition control
- Timing calculations
- Error handling
- Status monitoring

### TcpIpController
Low-level communication handling:
- TCP/IP connection management
- Command sending/receiving
- Protocol implementation
- Basic error checking

## Command Reference

Available commands through the TcpIpController:

| Command | Description | Response Expected |
|---------|-------------|------------------|
| OBSERVE | Start observation | No |
| STATUS | Get system status | Yes |
| START n | Start n acquisition cycles | No |
| STOP | Stop acquisition | No |
| SAVE name | Save data to file | No |
| DELETE | Clear data buffer | No |
| WDIR path | Set working directory | No |

## Timing Details

Timing calculations are based on the spectrometer's clock frequency:
```python
cycle_time_ms = (2460 / clock_frequency) * 1000
```

Safety margins:
- Minimum wait: 60% of theoretical time
- Timeout: theoretical time + 10 cycles
- Status confirmation: 2 consecutive IDLE states

## Error Handling

The library implements multiple layers of error handling:

1. Connection-level errors
2. Command validation
3. Response verification
4. Timeout protection
5. Status monitoring
6. Resource cleanup

## Logging

Uses loguru for comprehensive logging:
- Debug level: Command details
- Info level: Operation status
- Warning level: Timing issues
- Error level: Operation failures
- Trace level: Detailed status

## Requirements

- Python ≤ 3.12.9 (for telnetlib) or telnetlib3 when using Python ≥ 3.13
- asyncio
- loguru

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Based on the GHOST spectrometer software communication protocol.

## Development Setup

For development work:

1. Clone the repository as described above
2. Install development dependencies:
```bash
pip install -r requirements.txt
```

3. Setup pre-commit hooks:
```bash
pre-commit install
```

## Repository

The project is hosted on GitLab at the University of Hannover:
https://gitlab.uni-hannover.de/phytophotonics/ghosty (internal use)
and publically available hosted at GitHub:
https://github.com/timm-landes/ghosty

## Authors

**Project Lead:**
- Timm Landes
  - Leibniz University Hannover
  - Email: timm.landes@hot.uni-hannover.de
  - ORCID: https://orcid.org/0000-0001-8953-3003

**Contributors:**
- Dag Heinemann
  - Leibniz University Hannover
  - Email: da.heinemann@hot.uni-hannover.de
  - ORCID: https://orcid.org/0000-0003-3506-1762

## Citing Ghosty

If you use Ghosty in your research, please cite it as follows:

### BibTeX
```bibtex
@software{ghosty2024,
  author       = {Landes, Timm and Heinemann, Dag},
  title        = {Ghosty: A Python Interface for GHOST Brillouin Spectrometer Control},
  year         = {2025},
  version      = {0.1.1},
  url          = {https://gitlab.uni-hannover.de/phytophotonics/ghosty},
  institution  = {Leibniz University Hannover}
}
```

### APA Style
```
Landes, T., & Heinemann, D. (2025). Ghosty: A Python Interface for GHOST Brillouin 
Spectrometer Control (Version 0.1.1) [Computer software]. 
Leibniz University Hannover. https://gitlab.uni-hannover.de/phytophotonics/ghosty
```

### Related Publications
If applicable, please also cite the following related publications:
```
Landes, T., Khanal, B.P., Bethge, H.L. et al. Micromechanical behavior of the apple fruit cuticle investigated by Brillouin light scattering microscopy. Commun Biol 8, 174 (2025). https://doi.org/10.1038/s42003-025-07555-5
```