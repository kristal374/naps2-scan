from __future__ import annotations

import pytest

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.core.scanner import CoreScanner, list_devices
from naps2_scan.enums import ColorMode, Driver
from naps2_scan.types import ScanDevice


def test_list_devices(fake_bridge) -> None:
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = list_devices(driver=Driver.WIA, timeout=1.0)

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_core_scanner_context_manager(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with CoreScanner(device) as scanner:
        assert scanner.device is device
        assert scanner.worker.worker_id in bridge._workers

    assert scanner.worker.worker_id not in bridge._workers


def test_core_scanner_open_close(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)

    scanner.open()
    assert scanner.worker.worker_id in bridge._workers

    scanner.close()
    assert scanner.worker.worker_id not in bridge._workers


def test_core_scanner_double_open_is_idempotent(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)

    scanner.open()
    assert len(bridge._workers) == 1

    scanner.open()
    assert len(bridge._workers) == 1

    scanner.close()
    assert len(bridge._workers) == 0


def test_core_scanner_double_close_does_not_raise(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()
    scanner.close()

    scanner.close()


def test_core_scanner_context_manager_exception_propagates(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with pytest.raises(ValueError, match="test error"):
        with CoreScanner(device) as scanner:
            assert scanner.worker.worker_id in bridge._workers
            raise ValueError("test error")

    assert scanner.worker.worker_id not in bridge._workers


def test_core_scanner_capabilities(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        caps = scanner.capabilities()

        assert caps.flatbed is not None
        assert caps.flatbed.max_dpi == 300
    finally:
        scanner.close()


def test_core_scanner_scan(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        images = list(scanner.scan())

        assert len(images) == 1
    finally:
        scanner.close()


def test_core_scanner_scan_with_options(fake_bridge, sample_image) -> None:
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


def test_list_devices_default_driver(fake_bridge) -> None:
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = list_devices()

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_core_scanner_stop(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        scanner.stop()
        assert scanner.worker._cancel_scan_token is None
    finally:
        scanner.close()


def test_core_scanner_stop_then_scan_again(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        scanner.stop()

        images = list(scanner.scan())
        assert len(images) == 1
    finally:
        scanner.close()


def test_core_scanner_break_generator_then_rescan(fake_bridge, sample_image) -> None:
    images_data = [sample_image, sample_image.copy()]
    fake_bridge._scan_result = images_data
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        gen = scanner.scan()
        first = next(gen)
        assert first is not None
        # break without exhausting the generator
        gen.close()

        # rescan should work
        fake_bridge._scan_result = [sample_image]
        images = list(scanner.scan())
        assert len(images) == 1
    finally:
        scanner.close()


def test_core_scanner_callback_exception_on_scan_start(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        gen = scanner.scan(
            on_scan_start=lambda: (_ for _ in ()).throw(ValueError("callback error")),
        )
        with pytest.raises(Exception, match="callback error"):
            next(gen)
    finally:
        scanner.close()

    assert scanner.worker._cancel_scan_token is None


def test_core_scanner_callback_exception_on_page_start(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = CoreScanner(device)
    scanner.open()

    try:
        gen = scanner.scan(
            on_page_start=lambda n: (_ for _ in ()).throw(ValueError("page error")),
        )
        with pytest.raises(Exception, match="page error"):
            next(gen)
    finally:
        scanner.close()

    assert scanner.worker._cancel_scan_token is None
