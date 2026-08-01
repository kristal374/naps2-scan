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
)
from .images import Image, JpegImage, PngImage, ScannedImage
from .scanner import Scanner, list_devices
from .types import (
    CustomPageSize,
    PageSize,
    PerSourceCapabilities,
    ScanCapabilities,
    ScanDevice,
    ScanOptions,
)

__all__ = [
    "list_devices",
    "Scanner",
    "ScanDevice",
    "ScanOptions",
    "ScanCapabilities",
    "PerSourceCapabilities",
    "CustomPageSize",
    "PageSize",
    "PageSizeName",
    "PageSizeUnit",
    "Driver",
    "ColorMode",
    "PaperSource",
    "PixelFormat",
    "ImageFormat",
    "Image",
    "ScannedImage",
    "PngImage",
    "JpegImage",
    "ScannerError",
    "DeviceOfflineError",
    "DeviceNotFoundError",
    "ScanCancelledError",
    "ScanDriverError",
    "ValidationError",
]

__version__ = "0.1.0"
