# naps2-scan

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen.svg)](https://github.com/kristal374/naps2-scan)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/type-mypy-df5f00.svg)](https://mypy-lang.org/)
[![CI](https://github.com/kristal374/naps2-scan/actions/workflows/ci.yml/badge.svg)](https://github.com/kristal374/naps2-scan/actions/workflows/ci.yml)

Python wrapper over [NAPS2.Sdk](https://www.naps2.com/) via [pythonnet](https://github.com/pythonnet/pythonnet).  
Cross-platform scanner discovery and image acquisition on **Windows**, **macOS**, and **Linux**.

## Installation

```bash
pip install naps2-scan
```

> Requires .NET 8 SDK for building the native component during installation.  

## Quick Start

```python
from naps2_scan import Scanner, list_devices, ScanOptions, ColorMode

devices = list_devices()
for d in devices:
    print(f"{d.name} ({d.driver})")

with Scanner(devices[0]) as scanner:
    for i, img in enumerate(scanner.scan(dpi=300, color_mode=ColorMode.COLOR), 1):
        img.save(f"page_{i}.png")
```

### Async

```python
import asyncio
from naps2_scan import AsyncScanner, async_list_devices, ScanOptions

async def main():
    devices = await async_list_devices()
    async with AsyncScanner(devices[0]) as scanner:
        async for img in scanner.scan(dpi=150):
            print(img.width, img.height)

asyncio.run(main())
```

## Development

```bash
git clone https://github.com/kristal374/naps2-scan
cd naps2-scan
uv sync
```

### Running Tests

```bash
# Unit tests (no scanner hardware required)
uv run pytest tests/ -q --ignore=tests/test_real_scanner.py

# With coverage
uv run pytest tests/ -q --cov-report=term-missing --ignore=tests/test_real_scanner.py

# Real scanner tests (requires a connected scanner)
NAPS2_BRIDGE_RUN_HARDWARE_TESTS=1 uv run pytest -q -m real_scanner -s
```

## License

This project is licensed under the [MIT License](LICENSE).

This project uses NAPS2.SDK, which is licensed under
the GNU Lesser General Public License v2.1 (LGPL-2.1).
