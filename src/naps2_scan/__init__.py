"""naps2_scan — Python wrapper over NAPS2.Sdk via pythonnet."""

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
