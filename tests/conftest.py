from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from PIL import Image

from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.types import ScannerCapabilities


class FakeTask:
    def __init__(self, result=None, wait_side_effect=None):
        self._result = result
        self._wait_side_effect = wait_side_effect

    def GetAwaiter(self):
        return self

    def GetResult(self):
        return self._result

    def Wait(self):
        if self._wait_side_effect is not None:
            self._wait_side_effect()


class FakeBridge:
    def __init__(self):
        self.Initialize = MagicMock()
        self.Shutdown = MagicMock()
        self._devices = []
        self._scan_result = None
        self._scan_exception = None

    def GetDevicesAsync(self, driver, timeout=0):
        return FakeTask(json.dumps(self._devices))

    def GetCapabilitiesAsync(self, device_json):
        return FakeTask(
            ScannerCapabilities(
                metadata={},
                flatbed={
                    "type": "flatbed",
                    "resolutions": [100, 300],
                    "colorModes": ["color", "gray"],
                },
            ).model_dump_json(by_alias=True)
        )

    def ScanAsync(self, options_json, on_start, on_end, on_page_start, on_page_end,
                  on_page, on_progress, token):
        def run():
            if self._scan_exception is not None:
                raise self._scan_exception
            if on_start:
                on_start()
            for i, image in enumerate(self._scan_result or []):
                if on_page_start:
                    on_page_start(i + 1)
                if on_progress:
                    on_progress(i + 1, 50.0)
                if on_page:
                    raw = image.tobytes()
                    on_page(raw, image.width, image.height, image.mode)
                if on_page_end:
                    on_page_end(i + 1)
            if on_end:
                on_end()

        task = FakeTask(wait_side_effect=run)
        return task


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr("naps2_scan.core.bridge.Bridge", FakeBridge())
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False
    yield
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False


@pytest.fixture
def fake_bridge():
    return NAPS2Bridge()._open()


@pytest.fixture
def sample_image():
    return Image.new("RGB", (10, 10), color=(128, 128, 128))
