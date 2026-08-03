from __future__ import annotations

from typing import Any

from naps2_bridge.enums import ColorMode, Driver, PaperSource
from naps2_bridge.types import PageSize, ScanDevice, ScanOptions


def to_scan_device(obj: ScanDevice) -> Any:
    raise NotImplementedError


def from_scan_device(obj: Any) -> ScanDevice:
    raise NotImplementedError


def to_scan_options(options: ScanOptions, device: ScanDevice) -> Any:
    raise NotImplementedError


def to_page_size(page_size: PageSize) -> Any:
    raise NotImplementedError


def to_driver(driver: Driver) -> Any:
    raise NotImplementedError


def to_color_mode(mode: ColorMode) -> Any:
    raise NotImplementedError


def to_paper_source(source: PaperSource) -> Any:
    raise NotImplementedError


def to_pixel_format(pixel_format: Any) -> Any:
    raise NotImplementedError
