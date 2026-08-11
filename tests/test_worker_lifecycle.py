from __future__ import annotations

import pytest

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.core.scanner import CoreScanner
from naps2_scan.enums import Driver
from naps2_scan.types import ScanDevice


class FakeBridge:
    def __init__(self):
        self._initialized = False
        self._registered_workers: set = set()

    def Initialize(self):
        self._initialized = True

    def Shutdown(self):
        self._initialized = False
        self._registered_workers.clear()

    def GetDevicesAsync(self, driver, timeout=0):
        from conftest import FakeTask
        return FakeTask('[]')

    def GetCapabilitiesAsync(self, device_json):
        from conftest import FakeTask
        return FakeTask('{"metadata": null, "flatbed": null, "feeder": null, "duplex": null}')

    def ScanAsync(self, options_json, on_start, on_end, on_page_start, on_page_end,
                  on_page, on_progress, token):
        from conftest import FakeTask
        return FakeTask()


_fake_bridge_instance: FakeBridge | None = None


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    global _fake_bridge_instance
    _fake_bridge_instance = FakeBridge()
    monkeypatch.setattr("naps2_scan.core.bridge.Bridge", _fake_bridge_instance)
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False
    yield
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False


def test_open_close_balances_worker_registration() -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")
    scanner = CoreScanner(device)

    scanner.open()
    assert len(bridge._workers) == 1

    scanner.close()
    assert len(bridge._workers) == 0


def test_context_manager_balances_worker_registration() -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")

    with CoreScanner(device) as scanner:
        assert len(bridge._workers) == 1
        _ = scanner

    assert len(bridge._workers) == 0


def test_scan_without_open_raises() -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Fake")
    scanner = CoreScanner(device)

    with pytest.raises(RuntimeError, match="No connection established"):
        next(scanner.scan())
