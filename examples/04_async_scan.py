"""Async scan with async for loop."""

import asyncio
from pprint import pprint

from naps2_scan import AsyncScanner, async_list_devices


async def main() -> None:
    devices = await async_list_devices()

    print(f"Found {len(devices)} device(s):")
    for d in devices:
        print(f"\t{d.name} ({d.driver})")

    device = devices[0]
    async with AsyncScanner(device) as scanner:
        caps = await scanner.capabilities()
        pprint(caps.model_dump())

        async for image in scanner.scan():
            print(f"Page: {image.width}x{image.height} {image.mode}")


if __name__ == "__main__":
    asyncio.run(main())
