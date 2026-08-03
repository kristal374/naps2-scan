from __future__ import annotations

from typing import Callable, Iterator, List, Optional

from naps2_bridge.enums import Driver
from naps2_bridge.images import ScannedImage
from naps2_bridge.types import ScannerCapabilities, ScanDevice, ScanOptions


def list_devices(driver: Optional[Driver] = None, timeout: Optional[float] = None) -> List[ScanDevice]:
    raise NotImplementedError


class ScannerRuntime:
    def __init__(self, device: ScanDevice) -> None:
        self._device = device
        self._opened = False

    def open(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def capabilities(self) -> ScannerCapabilities:
        raise NotImplementedError

    def scan(
        self,
        options: Optional[ScanOptions],
        *,
        on_scan_start: Optional[Callable[[], None]] = None,
        on_scan_end: Optional[Callable[[], None]] = None,
        on_page_start: Optional[Callable[[int], None]] = None,
        on_page_progress: Optional[Callable[[int, float], None]] = None,
        on_page_end: Optional[Callable[[int, ScannedImage], None]] = None,
        **kwargs,
    ) -> Iterator[ScannedImage]:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError
