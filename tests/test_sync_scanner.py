from __future__ import annotations

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.enums import Driver
from naps2_scan.sync.scanner import Scanner, list_devices
from naps2_scan.types import ScanDevice


def test_list_devices(fake_bridge) -> None:
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = list_devices(driver=Driver.WIA, timeout=1.0)

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_scanner_context_manager(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with Scanner(device) as scanner:
        assert scanner.device is device
        assert scanner._core.worker.worker_id in bridge._workers

    assert scanner._core.worker.worker_id not in bridge._workers


def test_scanner_capabilities(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = Scanner(device)
    scanner.open()

    try:
        caps = scanner.capabilities()

        assert caps.flatbed is not None
    finally:
        scanner.close()


def test_scanner_scan(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = Scanner(device)
    scanner.open()

    try:
        images = list(scanner.scan())

        assert len(images) == 1
    finally:
        scanner.close()


def test_scanner_stop(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = Scanner(device)
    scanner.open()

    try:
        scanner.stop()
        assert scanner._core.worker._cancel_scan_token is None
    finally:
        scanner.close()
