from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional, Self

from PIL.Image import Image

from ..core.scanner import CoreScanner, list_devices as core_list_devices
from ..types import (
    PageCallback,
    ProgressCallback,
    StartCallback,
    OptionalArg,
    UNSET_VALUE,
    PageSize,
    DPI,
    Driver,
    ScanDevice,
    ScannerCapabilities,
    ScanOptions,
    ColorMode,
    PaperSource
)


async def async_list_devices(
        driver: Driver = Driver.DEFAULT,
        *,
        timeout: Optional[float] = None
) -> List[ScanDevice]:
    return await asyncio.to_thread(
        core_list_devices,
        driver=driver,
        timeout=timeout
    )


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

            on_scan_start: Optional[StartCallback] = None,
            on_scan_end: Optional[StartCallback] = None,
            on_page_start: Optional[PageCallback] = None,
            on_page_progress: Optional[ProgressCallback] = None,
            on_page_end: Optional[PageCallback] = None,

            options: ScanOptions = ScanOptions(),
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
            options=options,
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

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
