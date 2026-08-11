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
    with APIWorker() as worker:
        result = asyncio.run(worker.list_devices(driver=driver, timeout=timeout))
    return result


class CoreScanner:
    def __init__(self, device: ScanDevice) -> None:
        self.worker = APIWorker()
        self._device = device

    @property
    def device(self) -> ScanDevice:
        return self._device

    def __enter__(self) -> Self:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def open(self) -> Self:
        self.worker.create()
        return self

    def close(self) -> None:
        self.worker.delete()

    def capabilities(self) -> ScannerCapabilities:
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
        self.worker.stop()
