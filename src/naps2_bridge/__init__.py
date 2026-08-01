"""naps2_bridge — Python wrapper over NAPS2.Sdk via pythonnet."""

from .enums import (
    ColorMode,
    Driver,
    ImageFormat,
    PageSizeName,
    PageSizeUnit,
    PaperSource,
    PixelFormat,
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
from .images import ScannedImageMetadata, ScannedImage
from .scanner import Scanner, list_devices
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
    "list_devices",
    "Scanner",
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
    "PixelFormat",
    "ImageFormat",
    "ScannedImageMetadata",
    "ScannedImage",
    "ScannerError",
    "DeviceOfflineError",
    "DeviceNotFoundError",
    "ScanCancelledError",
    "ScanDriverError",
    "ValidationError",
    "UnsupportedPixelFormatError",
]

__version__ = "0.1.0"
