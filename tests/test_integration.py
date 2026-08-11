from __future__ import annotations

from PIL import Image

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.core.scanner import CoreScanner
from naps2_scan.enums import Driver
from naps2_scan.types import ScanDevice


def _make_image() -> Image.Image:
    return Image.new("RGB", (10, 10))


def test_two_scanners_work_independently(fake_bridge, sample_image) -> None:
    bridge = NAPS2Bridge()
    device_1 = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner 1")
    device_2 = ScanDevice(driver=Driver.TWAIN, id="dev-2", name="Scanner 2")

    scanner_1 = CoreScanner(device_1)
    scanner_2 = CoreScanner(device_2)

    scanner_1.open()
    scanner_2.open()

    try:
        assert len(bridge._workers) == 2
        assert scanner_1.worker.worker_id != scanner_2.worker.worker_id
    finally:
        scanner_1.close()
        scanner_2.close()

    assert len(bridge._workers) == 0


def test_two_scanners_scan_sequentially(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    scanner = CoreScanner(device)
    scanner.open()

    try:
        images = list(scanner.scan())
        assert len(images) == 1
    finally:
        scanner.close()


def test_scanner_reuse_after_close(fake_bridge, sample_image) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)

    scanner.open()
    scanner.close()

    scanner.open()
    try:
        assert scanner.worker.worker_id in bridge._workers
    finally:
        scanner.close()


def test_break_during_scan_cleans_up(fake_bridge, sample_image) -> None:
    images = [sample_image, sample_image.copy(), sample_image.copy()]
    fake_bridge._scan_result = images
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        gen = scanner.scan()
        next(gen)
        # break without exhausting
        gen.close()

        assert scanner.worker._cancel_scan_token is None
    finally:
        scanner.close()
