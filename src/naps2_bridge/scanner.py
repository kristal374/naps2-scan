"""Scanner discovery and connection API."""

from __future__ import annotations

from typing import Callable, Iterator, List, Optional, Protocol

from .enums import ColorMode, Driver, PaperSource
from .images import ScannedImage
from .types import PageSize, ScannerCapabilities, ScanDevice, ScanOptions, DPI, UNSET_VALUE, OptionalArg

StartCallback = Callable[[], None]


class ProgressCallback(Protocol):
    def __call__(self, page_number: int, progress: float) -> None: ...


class PageCallback(Protocol):
    def __call__(self, page_number: int, image: ScannedImage) -> None: ...


def list_devices(
        driver: Optional[Driver] = None, *, timeout: Optional[float] = None
) -> List[ScanDevice]:
    """Discover available scanner devices.

    Args:
        driver: Restrict discovery to a specific driver. ``Driver.DEFAULT`` selects
            the platform default (WIA on Windows, SANE on Linux, Apple on macOS).
        timeout: Optional timeout in seconds for device discovery.

    Returns:
        A list of discovered devices.
    """
    raise NotImplementedError


class Scanner:
    """Connection to a specific scanner device.

    Supports both context-manager and explicit ``close()`` usage.
    """

    def __init__(self, device: ScanDevice) -> None:
        self._device = device
        self._is_opened_connection = False

    @property
    def device(self) -> ScanDevice:
        """The device this scanner is connected to."""
        return self._device

    def __enter__(self) -> Scanner:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def open(self) -> None:
        """Open the connection to the device."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the connection and release resources."""
        raise NotImplementedError

    def capabilities(self) -> ScannerCapabilities:
        """Query device capabilities."""
        raise NotImplementedError

    def scan(
            self,
            *,
            dpi: OptionalArg[DPI] = UNSET_VALUE,
            color_mode: OptionalArg[ColorMode] = UNSET_VALUE,
            paper_source: OptionalArg[PaperSource] = UNSET_VALUE,
            page_size: OptionalArg[PageSize] = UNSET_VALUE,
            brightness: OptionalArg[int] = UNSET_VALUE,
            contrast: OptionalArg[int] = UNSET_VALUE,
            brightness_contrast_after_scan: OptionalArg[bool] = UNSET_VALUE,
            use_native_ui: OptionalArg[bool] = UNSET_VALUE,

            on_scan_start: Optional[StartCallback] = None,
            on_scan_end: Optional[StartCallback] = None,
            on_page_start: Optional[PageCallback] = None,
            on_page_progress: Optional[ProgressCallback] = None,
            on_page_end: Optional[PageCallback] = None,

            options: Optional[ScanOptions] = None,
    ) -> Iterator[ScannedImage]:
        """Start scanning and yield scanned images.

        Args:
            on_scan_start: Called when scanning starts.
            on_scan_end: Called when scanning ends.
            on_page_start: Called when page scanning starts.
            on_page_progress: Called with progress updates for the current page.
            on_page_end: Called when page scanning ends, with the resulting image.

            options: Base scan options. If omitted, default options are used.
        Yields:
            Scanned images.

        Raises:
            ScanCancelledError: If scanning is cancelled via ``stop()`` or the
                caller breaks out of the iteration.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Cancel an ongoing scan.

        Safe to call from a callback or another thread.
        """
        raise NotImplementedError
