"""Basic sync scan with options and file output."""

from pprint import pprint

from naps2_scan import Scanner, list_devices
from naps2_scan.enums import ColorMode, PageSizeUnit, PaperSource
from naps2_scan.types import CustomPageSize

devices = list_devices()

print(f"Found {len(devices)} device(s):")
for d in devices:
    print(f"\t{d.name} ({d.driver})")

device = devices[0]
with Scanner(device) as scanner:
    caps = scanner.capabilities()
    pprint(caps.model_dump())

    for image in scanner.scan(
        dpi=300,
        color_mode=ColorMode.COLOR,
        paper_source=PaperSource.FLATBED,
        page_size=CustomPageSize(width=210, height=297, unit=PageSizeUnit.MM),
        brightness=0,
        contrast=0,
    ):
        print(f"Image {image.width}x{image.height} {image.mode}")
        rgb_image = image.convert("RGB")
        rgb_image.save("scan_image.jpg")
