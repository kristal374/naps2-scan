from __future__ import annotations

import asyncio

import pytest

from naps2_scan.asyncio.scanner import AsyncScanner, async_list_devices
from naps2_scan.core.bridge import NAPS2Bridge
from naps2_scan.enums import Driver
from naps2_scan.types import ScanDevice


def test_async_list_devices(fake_bridge) -> None:
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = asyncio.run(async_list_devices(driver=Driver.WIA, timeout=1.0))

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_async_scanner_context_manager(fake_bridge) -> None:
    bridge = NAPS2Bridge()
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    async def run():
        async with AsyncScanner(device) as scanner:
            assert scanner.device is device
            assert scanner._core.worker.worker_id in bridge._workers
        assert scanner._core.worker.worker_id not in bridge._workers

    asyncio.run(run())


def test_async_scanner_capabilities(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            caps = await scanner.capabilities()
            assert caps.flatbed is not None
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_scan(fake_bridge, sample_image) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            images = [img async for img in scanner.scan()]
            assert len(images) == 1
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_scan_multiple_images(fake_bridge, sample_image) -> None:
    images_data = [sample_image, sample_image.copy()]
    fake_bridge._scan_result = images_data
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            images = [img async for img in scanner.scan()]
            assert len(images) == 2
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_scan_does_not_block_event_loop(
    fake_bridge, sample_image
) -> None:
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            concurrent_tasks = []

            async def concurrent_work():
                concurrent_tasks.append("ran")

            async def consume():
                images = []
                async for img in scanner.scan():
                    images.append(img)
                return images

            scan_task = asyncio.create_task(consume())
            await asyncio.sleep(0)
            await concurrent_work()

            images = await scan_task
            assert len(images) == 1
            assert concurrent_tasks == ["ran"]
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_scan_propagates_error(fake_bridge, sample_image) -> None:
    fake_bridge._scan_exception = type("DeviceNotFoundException", (Exception,), {})(
        "missing"
    )
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            with pytest.raises(Exception, match="missing"):
                async for _img in scanner.scan():
                    pass
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_scan_break_cleans_up(fake_bridge, sample_image) -> None:
    images_data = [sample_image, sample_image.copy(), sample_image.copy()]
    fake_bridge._scan_result = images_data
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            count = 0
            async for _img in scanner.scan():
                count += 1
                if count >= 1:
                    break
            assert count == 1
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_stop(fake_bridge) -> None:
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            await scanner.stop()
            assert scanner._core.worker._cancel_scan_token is None
        finally:
            await scanner.close()

    asyncio.run(run())
