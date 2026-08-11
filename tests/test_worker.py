from __future__ import annotations

import asyncio
import threading
import time

import pytest
from PIL import Image

from conftest import FakeBridge, FakeTask
from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.core.worker import APIWorker
from naps2_scan.enums import Driver
from naps2_scan.exceptions import DeviceNotFoundError
from naps2_scan.types import ScanDevice


class FakeToken:
    def __init__(self):
        self.Token = self
        self.cancelled = False

    def Cancel(self):
        self.cancelled = True


def _make_image(width: int = 10, height: int = 10, mode: str = "RGB") -> Image.Image:
    return Image.new(mode, (width, height), color=(128, 128, 128)[:len(mode)])


@pytest.fixture
def worker():
    return APIWorker().create()


def test_connection_raises_before_create() -> None:
    worker = APIWorker()

    with pytest.raises(RuntimeError, match="No connection established"):
        _ = worker.connection


def test_create_and_delete(worker) -> None:
    bridge = NAPS2Bridge()
    assert worker.worker_id in bridge._workers

    worker.delete()

    assert worker.worker_id not in bridge._workers
    assert worker._connection is None


def test_context_manager() -> None:
    bridge = NAPS2Bridge()

    with APIWorker() as worker:
        assert worker.worker_id in bridge._workers

    assert worker.worker_id not in bridge._workers


def test_list_devices_returns_devices(fake_bridge, worker) -> None:
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
        {"driver": "escl", "id": "dev-2", "name": "Scanner 2"},
    ]

    devices = asyncio.run(worker.list_devices())

    assert len(devices) == 2
    assert devices[0].id == "dev-1"
    assert devices[0].driver == Driver.WIA
    assert devices[1].driver == Driver.ESCL


def test_get_capabilities(fake_bridge, worker) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    caps = asyncio.run(worker.get_capabilities(device))

    assert caps.flatbed is not None
    assert caps.flatbed.min_dpi == 100
    assert caps.flatbed.max_dpi == 300


def test_scan_returns_images(fake_bridge, worker) -> None:
    images = [_make_image(), _make_image()]
    fake_bridge._scan_result = images
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    results = list(worker.scan(device))

    assert len(results) == 2
    assert all(isinstance(img, Image.Image) for img in results)


def test_scan_callbacks_fired(fake_bridge, worker) -> None:
    images = [_make_image()]
    fake_bridge._scan_result = images
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    events = []

    list(worker.scan(
        device,
        on_scan_start=lambda: events.append("start"),
        on_scan_end=lambda: events.append("end"),
        on_page_start=lambda n: events.append(("page_start", n)),
        on_page_end=lambda n: events.append(("page_end", n)),
        on_page_progress=lambda n, p: events.append(("progress", n, p)),
    ))

    assert "start" in events
    assert "end" in events
    assert ("page_start", 1) in events
    assert ("page_end", 1) in events
    assert ("progress", 1, 50.0) in events


def test_scan_wraps_exception(fake_bridge, worker) -> None:
    fake_bridge._scan_exception = type("DeviceNotFoundException", (Exception,), {})("missing")
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with pytest.raises(DeviceNotFoundError, match="missing"):
        next(worker.scan(device))


def test_scan_cleanup_drains_queue_and_stops_token(fake_bridge, worker) -> None:
    image = _make_image()

    class SlowFakeBridge(FakeBridge):
        def ScanAsync(self, *args, **kwargs):
            on_page = args[5]

            def background():
                raw = image.tobytes()
                on_page(raw, image.width, image.height, image.mode)
                time.sleep(0.5)

            threading.Thread(target=background).start()
            return FakeTask(wait_side_effect=lambda: None)

    worker._connection = SlowFakeBridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    for img in worker.scan(device):
        assert img is not None
        break

    assert worker._cancel_scan_token is None


def test_stop_cancels_token(worker) -> None:
    token = FakeToken()
    worker._cancel_scan_token = token

    worker.stop()

    assert token.cancelled


def test_scan_cleanup_handles_empty_queue(worker) -> None:
    images = [_make_image(), _make_image()]

    class SlowProducerBridge(FakeBridge):
        def ScanAsync(self, *args, **kwargs):
            on_page = args[5]

            def background():
                for image in images:
                    raw = image.tobytes()
                    on_page(raw, image.width, image.height, image.mode)
                    time.sleep(3.0)

            threading.Thread(target=background).start()
            return FakeTask(wait_side_effect=lambda: None)

    worker._connection = SlowProducerBridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    for img in worker.scan(device):
        assert img is not None
        break

    assert worker._cancel_scan_token is None


def test_scan_rejects_concurrent(worker) -> None:
    scan_started = threading.Event()
    release_scan = threading.Event()

    class SlowFakeBridge(FakeBridge):
        def ScanAsync(self, *args, **kwargs):
            def run():
                scan_started.set()
                release_scan.wait()

            return FakeTask(wait_side_effect=run)

    worker._connection = SlowFakeBridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    def scan_in_thread():
        for _ in worker.scan(device):
            pass

    t = threading.Thread(target=scan_in_thread)
    t.start()
    scan_started.wait(timeout=2)

    try:
        with pytest.raises(RuntimeError, match="already busy"):
            next(worker.scan(device))
    finally:
        release_scan.set()
        t.join(timeout=5)


def test_stop_without_token_does_not_raise(worker) -> None:
    worker._cancel_scan_token = None
    worker.stop()


def test_scan_without_connection_raises() -> None:
    worker = APIWorker()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    with pytest.raises(RuntimeError, match="No connection established"):
        next(worker.scan(device))


def test_scan_generator_exception_stops_token(worker) -> None:
    images = [_make_image()]
    local_bridge = FakeBridge()
    local_bridge._scan_result = images
    worker._connection = local_bridge
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    gen = worker.scan(device)
    next(gen)

    gen.close()

    assert worker._cancel_scan_token is None


def test_scan_corrupt_image_data_does_not_hang(worker) -> None:
    class CorruptBridge(FakeBridge):
        def ScanAsync(self, *args, **kwargs):
            on_page = args[5]

            def background():
                try:
                    on_page(b"not enough bytes", 10, 10, "RGB")
                except ValueError:
                    pass

            threading.Thread(target=background, daemon=True).start()
            return FakeTask(wait_side_effect=lambda: None)

    worker._connection = CorruptBridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    images = list(worker.scan(device))
    assert len(images) == 0
