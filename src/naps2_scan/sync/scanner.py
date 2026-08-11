"""Synchronous scanner API.

The :class:`Scanner` class is the recommended entry point for
single-threaded / script usage.  It provides a context manager and
returns a blocking iterator from :meth:`Scanner.scan`.

```python
>>> from naps2_scan import Scanner, list_devices
>>> devices = list_devices()
>>> with Scanner(devices[0]) as s:
...     for img in s.scan(dpi=300):
...         img.save("page.png")
```
"""

from __future__ import annotations

from collections.abc import Iterator
from types import TracebackType
from typing import Self

from PIL.Image import Image

from ..core.scanner import CoreScanner
from ..core.scanner import list_devices as core_list_devices
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


def list_devices(
    driver: Driver = Driver.DEFAULT, *, timeout: float | None = None
) -> list[ScanDevice]:
    """Synchronous wrapper for :func:`naps2_scan.core.scanner.list_devices`.

    See that function for full documentation.
    """
    return core_list_devices(driver=driver, timeout=timeout)


class Scanner:
    """Synchronous scanner for a single device.

    All methods block the calling thread.  The scanner can be used as a
    context manager (``with Scanner(device) as s:``) which calls
    :meth:`open` / :meth:`close` automatically.

    Args:
        device: The :class:`ScanDevice` to use, obtained from
            :func:`list_devices`.

    Example:
        >>> from naps2_scan import Scanner, list_devices, ScanOptions, ColorMode
        >>> devices = list_devices()
        >>> with Scanner(devices[0]) as scanner:
        ...     caps = scanner.capabilities()
        ...     for i, img in enumerate(scanner.scan(
        ...         options=ScanOptions(dpi=300, color_mode=ColorMode.COLOR),
        ...     ), 1):
        ...         img.save(f'page_{i}.png')
    """

    def __init__(self, device: ScanDevice):
        self._core = CoreScanner(device=device)

    @property
    def device(self) -> ScanDevice:
        """The :class:`ScanDevice` this scanner is bound to."""
        return self._core.device

    def open(self) -> Self:
        """Connect to the scanner. Called automatically by the context manager."""
        self._core.open()
        return self

    def capabilities(self) -> ScannerCapabilities:
        """Query the device's supported options.

        Returns:
            A :class:`ScannerCapabilities` object.
        """
        return self._core.capabilities()

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
        options: ScanOptions | None = None,
    ) -> Iterator[Image]:
        """Start scanning. See :meth:`CoreScanner.scan` for full docs."""
        return self._core.scan(
            dpi=dpi,
            color_mode=color_mode,
            paper_source=paper_source,
            page_size=page_size,
            brightness=brightness,
            contrast=contrast,
            brightness_contrast_after_scan=brightness_contrast_after_scan,
            use_native_ui=use_native_ui,
            on_scan_start=on_scan_start,
            on_scan_end=on_scan_end,
            on_page_start=on_page_start,
            on_page_progress=on_page_progress,
            on_page_end=on_page_end,
            options=options if options is not None else ScanOptions(),
        )

    def stop(self) -> None:
        """Cancel an in-progress scan."""
        self._core.stop()

    def close(self) -> None:
        """Disconnect from the scanner."""
        self._core.close()

    def __enter__(self) -> Self:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
