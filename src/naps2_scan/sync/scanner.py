from __future__ import annotations

from typing import Iterator, List, Optional, Self

from PIL.Image import Image

from ..core.scanner import CoreScanner, list_devices as core_list_devices
from ..types import (
    PageCallback,
    ProgressCallback,
    PageStartCallback,
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


def list_devices(
        driver: Driver = Driver.DEFAULT,
        *,
        timeout: Optional[float] = None
) -> List[ScanDevice]:
    return core_list_devices(driver=driver, timeout=timeout)


class Scanner:
    def __init__(self, device: ScanDevice):
        self._core = CoreScanner(device=device)

    @property
    def device(self) -> ScanDevice:
        return self._core.device

    def open(self) -> Self:
        self._core.open()
        return self

    def capabilities(self) -> ScannerCapabilities:
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

            on_scan_start: Optional[StartCallback] = None,
            on_scan_end: Optional[StartCallback] = None,
            on_page_start: Optional[PageStartCallback] = None,
            on_page_progress: Optional[ProgressCallback] = None,
            on_page_end: Optional[PageCallback] = None,

            options: ScanOptions = ScanOptions(),
    ) -> Iterator[Image]:
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
            options=options,
        )

    def stop(self) -> None:
        self._core.stop()

    def close(self) -> None:
        self._core.close()

    def __enter__(self) -> Self:
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
