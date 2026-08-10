"""naps2_scan — Python wrapper over NAPS2.Sdk via pythonnet."""

from .asyncio.scanner import AsyncScanner, async_list_devices
from .enums import (
    ColorMode,
    Driver,
    ImageFormat,
    PageSizeName,
    PageSizeUnit,
    PaperSource,
)
from .exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    ScanCancelledError,
    ScanDriverError,
    ScannerError,
    ValidationError,
    UnsupportedPixelFormatError,
)
from .sync.scanner import Scanner, list_devices
from .types import (
    CustomPageSize,
    ScanAreaSize,
    PageSize,
    ScannerCapabilities,
    SourceCapabilities,
    ScanDevice,
    ScanOptions,
)

__all__ = [
    "AsyncScanner",
    "async_list_devices",
    "Scanner",
    "list_devices",
    "ScanDevice",
    "ScanOptions",
    "ScannerCapabilities",
    "SourceCapabilities",
    "ScanAreaSize",
    "CustomPageSize",
    "PageSize",
    "PageSizeName",
    "PageSizeUnit",
    "Driver",
    "ColorMode",
    "PaperSource",
    "ImageFormat",
    "ScannerError",
    "DeviceOfflineError",
    "DeviceNotFoundError",
    "ScanCancelledError",
    "ScanDriverError",
    "ValidationError",
    "UnsupportedPixelFormatError",
]

__version__ = "0.1.0"
