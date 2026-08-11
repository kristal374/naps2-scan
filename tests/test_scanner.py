from __future__ import annotations

import pytest

from naps2_scan.core.scanner import CoreScanner, list_devices
from naps2_scan.enums import ColorMode, Driver
from naps2_scan.types import ScanDevice, ScanOptions


def test_list_devices(fake_bridge):
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = list_devices(driver=Driver.WIA, timeout=1.0)

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_core_scanner_context_manager(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with CoreScanner(device) as scanner:
        assert scanner.device is device


def test_core_scanner_open_close(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)

    scanner.open()
    assert scanner.worker.worker_id is not None

    scanner.close()


def test_core_scanner_capabilities(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        caps = scanner.capabilities()

        assert caps.flatbed is not None
        assert caps.flatbed.max_dpi == 300
    finally:
        scanner.close()


def test_core_scanner_scan(fake_bridge, sample_image):
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        images = list(scanner.scan())

        assert len(images) == 1
    finally:
        scanner.close()


def test_core_scanner_scan_with_options(fake_bridge, sample_image):
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    events = []

    try:
        list(scanner.scan(
            dpi=300,
            color_mode=ColorMode.COLOR,
            on_scan_start=lambda: events.append("start"),
        ))
    finally:
        scanner.close()

    assert events == ["start"]


def test_list_devices_default_driver(fake_bridge):
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = list_devices()

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_core_scanner_stop(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        scanner.stop()
    finally:
        scanner.close()
