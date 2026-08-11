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
    return await asyncio.to_thread(core_list_devices, driver=driver, timeout=timeout)


class AsyncScanner:
    def __init__(self, device: ScanDevice):
        self._core = CoreScanner(device=device)

    @property
    def device(self) -> ScanDevice:
        return self._core.device

    async def open(self) -> Self:
        await asyncio.to_thread(self._core.open)
        return self

    async def capabilities(self) -> ScannerCapabilities:
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
        return await asyncio.to_thread(self._core.stop)

    async def close(self) -> None:
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
