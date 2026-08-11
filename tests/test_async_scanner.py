from __future__ import annotations

import asyncio

import pytest

from naps2_scan.asyncio.scanner import AsyncScanner, async_list_devices
from naps2_scan.enums import Driver
from naps2_scan.types import ScanDevice


def test_async_list_devices(fake_bridge):
    fake_bridge._devices = [
        {"driver": "wia", "id": "dev-1", "name": "Scanner 1"},
    ]

    devices = asyncio.run(async_list_devices(driver=Driver.WIA, timeout=1.0))

    assert len(devices) == 1
    assert devices[0].id == "dev-1"


def test_async_scanner_context_manager(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")

    async def run():
        async with AsyncScanner(device) as scanner:
            assert scanner.device is device

    asyncio.run(run())


def test_async_scanner_capabilities(fake_bridge):
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


def test_async_scanner_scan(fake_bridge, sample_image):
    fake_bridge._scan_result = [sample_image]
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            images = list(await scanner.scan())
            assert len(images) == 1
        finally:
            await scanner.close()

    asyncio.run(run())


def test_async_scanner_stop(fake_bridge):
    device = ScanDevice(driver=Driver.WIA, id="dev-1", name="Scanner")
    scanner = AsyncScanner(device)

    async def run():
        await scanner.open()
        try:
            await scanner.stop()
        finally:
            await scanner.close()

    asyncio.run(run())
