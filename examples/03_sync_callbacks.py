"""Scan with all available callbacks."""

from naps2_scan import Scanner, list_devices


def on_scan_start() -> None:
    print("Scan started...")


def on_scan_end() -> None:
    print("Scan ended.")


def on_page_start(page_number: int) -> None:
    print(f"Page {page_number} scan started.")


def on_page_end(page_number: int) -> None:
    print(f"\nPage {page_number} scan ended.")


def on_page_progress(page_number: int, progress: float) -> None:
    print(f"\rPage {page_number}, progress={progress * 100:.0f}%", end="")


devices = list_devices()

print(f"Found {len(devices)} device(s):")
for d in devices:
    print(f"\t{d.name} ({d.driver})")

device = devices[0]
with Scanner(device) as scanner:
    for n, image in enumerate(
        scanner.scan(
            on_scan_start=on_scan_start,
            on_scan_end=on_scan_end,
            on_page_start=on_page_start,
            on_page_end=on_page_end,
            on_page_progress=on_page_progress,
        ),
        1,
    ):
        image.save(f"scan_page_{n}.png")
