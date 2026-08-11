from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from PIL import Image

from naps2_scan import Scanner, async_list_devices, list_devices
from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.enums import ColorMode
from naps2_scan.types import ScanOptions

pytestmark = pytest.mark.real_scanner


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the bridge singleton without installing the fake Bridge."""
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False
    yield
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False


def _should_run_hardware_tests() -> bool:
    return os.environ.get("NAPS2_BRIDGE_RUN_HARDWARE_TESTS", "").lower() in (
        "1",
        "true",
        "yes",
    )


@pytest.fixture(scope="module")
def real_device():
    if not _should_run_hardware_tests():
        pytest.skip("Set NAPS2_BRIDGE_RUN_HARDWARE_TESTS=1 to run real scanner tests")

    devices = list_devices()
    if not devices:
        pytest.skip("No scanners discovered")

    return devices[0]


@pytest.fixture(scope="module")
def scanner(real_device):
    with Scanner(real_device) as scanner:
        yield scanner


def test_list_real_devices():
    if not _should_run_hardware_tests():
        pytest.skip("Set NAPS2_BRIDGE_RUN_HARDWARE_TESTS=1 to run real scanner tests")

    devices = list_devices()
    assert len(devices) > 0
    for device in devices:
        assert device.id
        assert device.name
        assert device.driver


def test_capabilities(scanner):
    caps = scanner.capabilities()

    assert caps is not None
    assert len(caps.paper_sources) > 0
    for source in caps.paper_sources:
        assert source.type
        assert len(source.resolutions) > 0
        assert source.max_scan_area is not None


def test_scan_single_page(scanner, tmp_path: Path):
    options = ScanOptions(dpi=75, color_mode=ColorMode.GRAY)
    images = list(scanner.scan(options=options))

    assert len(images) == 1
    image = images[0]
    assert isinstance(image, Image.Image)
    assert image.mode in ("L", "RGB", "RGBA")
    assert image.width > 0
    assert image.height > 0


def test_scan_and_save_png(scanner, tmp_path: Path):
    options = ScanOptions(dpi=75, color_mode=ColorMode.GRAY)
    images = list(scanner.scan(options=options))

    assert len(images) == 1
    output = tmp_path / "scan.png"
    images[0].save(output, format="PNG")

    assert output.exists()
    assert output.stat().st_size > 0


def test_scan_and_save_jpeg(scanner, tmp_path: Path):
    options = ScanOptions(dpi=75, color_mode=ColorMode.GRAY)
    images = list(scanner.scan(options=options))

    assert len(images) == 1
    output = tmp_path / "scan.jpg"
    image = images[0]
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(output, format="JPEG")

    assert output.exists()
    assert output.stat().st_size > 0


def test_scan_callbacks(scanner):
    events = []

    options = ScanOptions(dpi=75, color_mode=ColorMode.GRAY)
    list(
        scanner.scan(
            options=options,
            on_scan_start=lambda: events.append("start"),
            on_scan_end=lambda: events.append("end"),
            on_page_start=lambda n: events.append(("page_start", n)),
            on_page_end=lambda n: events.append(("page_end", n)),
        )
    )

    assert "start" in events
    assert "end" in events
    assert ("page_start", 1) in events
    assert ("page_end", 1) in events


def test_async_list_real_devices():
    if not _should_run_hardware_tests():
        pytest.skip("Set NAPS2_BRIDGE_RUN_HARDWARE_TESTS=1 to run real scanner tests")

    devices = asyncio.run(async_list_devices())
    if not devices:
        pytest.skip("No scanners discovered")

    assert len(devices) > 0
    assert devices[0].id
