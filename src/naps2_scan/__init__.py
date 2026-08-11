"""naps2_scan — Python wrapper over NAPS2.Sdk via pythonnet.

Provides both synchronous and asynchronous APIs for scanner discovery
and image acquisition across Windows, macOS, and Linux.

Quick start::

    >>> from naps2_scan import Scanner, list_devices, ColorMode

    >>> devices = list_devices()
    >>> with Scanner(devices[0]) as scanner:
    ...     for img in scanner.scan(dpi=300, color_mode=ColorMode.COLOR)):
    ...         img.save("page.png")

Async::

    >>> from naps2_scan import AsyncScanner, async_list_devices, ColorMode

    >>> async def main():
    ...     devices = await async_list_devices()
    ...     async with AsyncScanner(devices[0]) as scanner:
    ...         async for img in scanner.scan(dpi=300, color_mode=ColorMode.COLOR)):
    ...             img.save("page.png")

Exports
-------
- :class:`Scanner` / :class:`AsyncScanner` — sync / async scanner sessions.
- :func:`list_devices` / :func:`async_list_devices` — discover scanners.
- :class:`ScanDevice`, :class:`ScanOptions`, :class:`ScannerCapabilities` —
  data models.
- :class:`ColorMode`, :class:`Driver`, :class:`PaperSource`,
  :class:`PageSizeName`, :class:`PageSizeUnit` — enums.
- :class:`CustomPageSize`, :class:`PageSize`, :class:`ScanAreaSize`,
  :class:`SourceCapabilities`, :class:`CapsMetadata` — supporting types.
- :class:`DPI` — type alias for resolution values.
- :class:`ScannerError` and subclasses — exception hierarchy.
"""

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
