"""naps2_scan — Python wrapper over NAPS2.Sdk via pythonnet."""

from .asyncio.scanner import AsyncScanner, async_list_devices
from .enums import (
    ColorMode,
    Driver,
    PageSizeName,
    PageSizeUnit,
    PaperSource,
)
from .exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    ScanCancelledError,
    ScanDriverError,
    ScanFailedError,
    ScannerError,
    UnsupportedPixelFormatError,
    ValidationError,
)
from .sync.scanner import Scanner, list_devices
from .types import (
    DPI,
    CapsMetadata,
    CustomPageSize,
    PageSize,
    ScanAreaSize,
    ScanDevice,
    ScannerCapabilities,
    ScanOptions,
    SourceCapabilities,
)

__all__ = [
    "DPI",
    "AsyncScanner",
    "CapsMetadata",
    "ColorMode",
    "CustomPageSize",
    "DeviceNotFoundError",
    "DeviceOfflineError",
    "Driver",
    "PageSize",
    "PageSizeName",
    "PageSizeUnit",
    "PaperSource",
    "ScanAreaSize",
    "ScanCancelledError",
    "ScanDevice",
    "ScanDriverError",
    "ScanFailedError",
    "ScanOptions",
    "Scanner",
    "ScannerCapabilities",
    "ScannerError",
    "SourceCapabilities",
    "UnsupportedPixelFormatError",
    "ValidationError",
    "async_list_devices",
    "list_devices",
]

__version__ = "0.1.0"
