from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.core.scanner import CoreScanner
from naps2_scan.enums import Driver
from naps2_scan.types import ScanDevice


class FakeBridge:
    _initialized = False
    _registered_workers: set = set()

    @staticmethod
    def Initialize():
        FakeBridge._initialized = True

    @staticmethod
    def Shutdown():
        FakeBridge._initialized = False
        FakeBridge._registered_workers.clear()

    @staticmethod
    def GetDevicesAsync(driver, timeout=0):
        task = MagicMock()
        task.GetAwaiter.return_value.GetResult.return_value = '[]'
        return task

    @staticmethod
    def GetCapabilitiesAsync(device_json):
        task = MagicMock()
        task.GetAwaiter.return_value.GetResult.return_value = (
            '{"metadata": null, "flatbed": null, "feeder": null, "duplex": null}'
        )
        return task

    @staticmethod
    def ScanAsync(options_json, on_start, on_end, on_page_start, on_page_end,
                  on_page, on_progress, token):
        return MagicMock()


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr("naps2_scan.core.bridge.Bridge", FakeBridge)
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False
    FakeBridge._initialized = False
    FakeBridge._registered_workers.clear()
    yield
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False


def test_open_close_balances_worker_registration():
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")
    scanner = CoreScanner(device)

    scanner.open()
    assert len(bridge._workers) == 1

    scanner.close()
    assert len(bridge._workers) == 0


def test_context_manager_balances_worker_registration():
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")

    with CoreScanner(device) as scanner:
        assert len(bridge._workers) == 1
        _ = scanner

    assert len(bridge._workers) == 0


def test_scan_without_open_raises():
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")
    scanner = CoreScanner(device)

    with pytest.raises(RuntimeError, match="No connection established"):
        next(scanner.scan())
