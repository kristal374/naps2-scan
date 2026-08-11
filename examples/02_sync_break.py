"""Break from scan generator to cancel remaining pages."""

from naps2_scan import ColorMode, Scanner, ScanOptions, list_devices

devices = list_devices()

print(f"Found {len(devices)} device(s):")
for d in devices:
    print(f"\t{d.name} ({d.driver})")

device = devices[0]
with Scanner(device) as scanner:
    options = ScanOptions(dpi=150, color_mode=ColorMode.GRAY)
    for image in scanner.scan(options=options):
        print(f"First page: {image.width}x{image.height}")
        break
