"""Core scanner implementation shared by both sync and async wrappers.

All blocking I/O is delegated to threads; the public sync and async APIs
in ``naps2_scan.sync`` and ``naps2_scan.asyncio`` wrap this module.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from types import TracebackType
from typing import Self

from PIL import Image

from ..enums import ColorMode, Driver, PaperSource
from ..types import (
    DPI,
    UNSET_VALUE,
    OptionalArg,
    PageCallback,
    PageSize,
    ProgressCallback,
    ScanDevice,
    ScannerCapabilities,
    ScanOptions,
    StartCallback,
)
from .worker import APIWorker


def list_devices(
    driver: Driver = Driver.DEFAULT, *, timeout: float | None = None
) -> list[ScanDevice]:
    """Discover available scanning devices.

    Args:
        driver: Driver type to probe. Default scans all drivers.
        timeout: Maximum time in seconds to wait for device discovery.
            ``None`` means no timeout.

    Returns:
        List of discovered :class:`ScanDevice` objects.

    Raises:
        ScannerError: If the NAPS2 bridge encounters an error during
            device enumeration.

    Example:
        >>> devices = list_devices()
        >>> for d in devices:
        ...     print(d.name, d.driver)
    """
    with APIWorker() as worker:
        result = asyncio.run(worker.list_devices(driver=driver, timeout=timeout))
    return result


class CoreScanner:
    """Low-level scanner session tied to a single device.

    All methods block the calling thread (internally they delegate work
    to a background thread).  Use :class:`~naps2_scan.Scanner` for a
    convenience wrapper or :class:`~naps2_scan.AsyncScanner` for
    ``async`` / ``await`` support.

    Args:
        device: The device to scan from, obtained from :func:`list_devices`.

    Example:
        >>> scanner = CoreScanner(...)
        >>> scanner.open()
        >>> caps = scanner.capabilities()
        >>> for img in scanner.scan(dpi=300):
        ...     img.save("page.png")
        >>> scanner.close()
    """

    def __init__(self, device: ScanDevice) -> None:
        self.worker = APIWorker()
        self._device = device

    @property
    def device(self) -> ScanDevice:
        """The :class:`ScanDevice` this scanner is bound to."""
        return self._device

    def __enter__(self) -> Self:
        """Context-manager entry — calls :meth:`open`."""
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context-manager exit — calls :meth:`close`."""
        self.close()

    def open(self) -> Self:
        """Connect to the scanner and register with the NAPS2 bridge.

        Must be called before :meth:`scan` or :meth:`capabilities`.
        """
        self.worker.create()
        return self

    def close(self) -> None:
        """Disconnect from the scanner and release bridge resources."""
        self.worker.delete()

    def capabilities(self) -> ScannerCapabilities:
        """Query the device's supported options.

        Returns:
            A :class:`ScannerCapabilities` object listing available
            paper sources, resolutions, color modes and scan area.
        """
        result = asyncio.run(self.worker.get_capabilities(device=self.device))
        return result

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
        on_scan_start: StartCallback | None = None,
        on_scan_end: StartCallback | None = None,
        on_page_start: PageCallback | None = None,
        on_page_progress: ProgressCallback | None = None,
        on_page_end: PageCallback | None = None,
        options: ScanOptions = ScanOptions(),  # noqa: B008
    ) -> Iterator[Image.Image]:
        """Start scanning and yield pages as :class:`PIL.Image.Image` objects.

        Options can be provided either as keyword arguments (which are
        merged with *options*) or via a pre-built :class:`ScanOptions`
        instance.  Keyword arguments take precedence.

        Args:
            dpi: Resolution in DPI.
            color_mode: :class:`ColorMode` (``"color"``, ``"gray"``, ``"bw"``).
            paper_source: :class:`PaperSource` (``"flatbed"``, ``"feeder"``, ``"duplex"``).
            page_size: Standard :class:`PageSizeName` or custom :class:`CustomPageSize`.
            brightness: Brightness adjustment.
            contrast: Contrast adjustment.
            brightness_contrast_after_scan: Apply brightness/contrast after the scan.
            use_native_ui: Show the scanner vendor's native UI dialog.
            on_scan_start: Called when the scan session begins.
            on_scan_end: Called when the scan session ends.
            on_page_start: Called with the page number when a new page starts.
            on_page_progress: Called with ``(page_number, progress_0_to_1)``
                during scanning.
            on_page_end: Called with the page number when a page finishes.
            options: Base :class:`ScanOptions` to merge keyword arguments into.

        Yields:
            One :class:`PIL.Image.Image` per scanned page.

        Raises:
            DeviceNotFoundError: The device is no longer available.
            DeviceOfflineError: The device is offline or unreachable.
            ScanCancelledError: The scan was canceled by :meth:`stop`.
            ScanDriverError: A driver-level error occurred (paper jam, etc.).
            ScanFailedError: The scan operation failed.
            ValidationError: The requested options are not valid for this device.

        Example:
            >>> from naps2_scan import Scanner
            >>> with Scanner(...) as scanner:
            ...     for i, img in enumerate(scanner.scan(dpi=300, color_mode=ColorMode.COLOR), 1):
            ...         img.save(f"page_{i}.png")
        """
        user_options = options.merge(
            dpi=dpi,
            color_mode=color_mode,
            paper_source=paper_source,
            page_size=page_size,
            brightness=brightness,
            contrast=contrast,
            brightness_contrast_after_scan=brightness_contrast_after_scan,
            use_native_ui=use_native_ui,
        )
        yield from self.worker.scan(
            device=self.device,
            options=user_options,
            on_scan_start=on_scan_start,
            on_scan_end=on_scan_end,
            on_page_start=on_page_start,
            on_page_progress=on_page_progress,
            on_page_end=on_page_end,
        )

    def stop(self) -> None:
        """Cancel an in-progress scan.

        Safe to call when no scan is active (does nothing).
        """
        self.worker.stop()
