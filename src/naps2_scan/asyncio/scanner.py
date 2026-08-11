"""Asynchronous scanner API for use with ``asyncio``.

The :class:`AsyncScanner` class supports ``async with`` and ``async for``:

```python
>>> import asyncio
>>> from naps2_scan import AsyncScanner, async_list_devices, ScanOptions
>>>
>>> async def main():
...     devices = await async_list_devices()
...     async with AsyncScanner(devices[0]) as scanner:
...         async for image in scanner.scan(dpi=300):
...             image.save("page.png")
>>>
>>> asyncio.run(main())
```

All blocking operations run in a thread pool so the event loop stays
responsive.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
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


async def async_list_devices(
    driver: Driver = Driver.DEFAULT, *, timeout: float | None = None
) -> list[ScanDevice]:
    """Async wrapper for :func:`~naps2_scan.core.scanner.list_devices`.

    Runs device discovery in a thread pool so the event loop is not
    blocked.  See :func:`list_devices` for full documentation.
    """
    return await asyncio.to_thread(core_list_devices, driver=driver, timeout=timeout)


class AsyncScanner:
    """Asynchronous scanner for a single device.

    All methods are coroutines.  The scanner can be used as an async
    context manager (``async with AsyncScanner(device) as s:``).

    Args:
        device: The :class:`ScanDevice` to use, obtained from
            :func:`async_list_devices`.

    Example:
        >>> from naps2_scan import AsyncScanner, async_list_devices, ScanOptions
        >>>
        >>> async def main():
        ...     devices = await async_list_devices()
        ...     async with AsyncScanner(devices[0]) as scanner:
        ...         async for img in scanner.scan(options=ScanOptions(dpi=150)):
        ...             print(img.width, img.height)

    """

    def __init__(self, device: ScanDevice):
        self._core = CoreScanner(device=device)

    @property
    def device(self) -> ScanDevice:
        """The :class:`ScanDevice` this scanner is bound to."""
        return self._core.device

    async def open(self) -> Self:
        """Connect to the scanner. Called automatically by the context manager."""
        await asyncio.to_thread(self._core.open)
        return self

    async def capabilities(self) -> ScannerCapabilities:
        """Query the device's supported options.

        Returns:
            A :class:`ScannerCapabilities` object.
        """
        return await asyncio.to_thread(self._core.capabilities)

    async def scan(
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
    ) -> AsyncIterator[Image]:
        """Start scanning. Yields pages asynchronously as they arrive.

        Each page is fetched in a thread pool so the event loop is not
        blocked.  See :meth:`CoreScanner.scan` for full parameter docs.

        Example:
            >>> from naps2_scan import AsyncScanner, ColorMode
            >>>
            >>> async def main():
            ...     async with AsyncScanner(...) as scanner:
            ...         async for image in scanner.scan(dpi=300, color_mode=ColorMode.COLOR):
            ...             image.save("page.png")
        """
        it = self._core.scan(
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

        def _next_item() -> Image | None:
            return next(it, None)

        try:
            while True:
                img = await asyncio.to_thread(_next_item)
                if img is None:
                    return
                yield img
        except GeneratorExit:
            await asyncio.to_thread(self._core.stop)
            raise

    async def stop(self) -> None:
        """Cancel an in-progress scan."""
        return await asyncio.to_thread(self._core.stop)

    async def close(self) -> None:
        """Disconnect from the scanner."""
        return await asyncio.to_thread(self._core.close)

    async def __aenter__(self) -> Self:
        return await self.open()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
