from __future__ import annotations

import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from naps2_scan.enums import ColorMode, Driver, PageSizeName, PageSizeUnit, PaperSource
from naps2_scan.types import (
    CapsMetadata,
    CustomPageSize,
    DPI,
    ScanAreaSize,
    ScanDevice,
    ScannerCapabilities,
    ScanOptions,
    SourceCapabilities,
    UNSET_VALUE,
)


def test_scan_device_accepts_driver_enum_and_string() -> None:
    from_enum = ScanDevice(driver=Driver.WIA, id="1", name="Scanner")
    from_str = ScanDevice(driver="wia", id="1", name="Scanner")

    assert from_enum.driver is Driver.WIA
    assert from_str.driver is Driver.WIA


def test_scan_device_normalizes_driver_case() -> None:
    device = ScanDevice(driver="WIA", id="1", name="Scanner")
    assert device.driver is Driver.WIA


def test_scan_device_serialization_uses_aliases() -> None:
    device = ScanDevice(
        driver=Driver.WIA,
        id="1",
        name="Scanner",
        icon_uri="icon://scanner",
        connection_uri="usb://scanner",
    )

    data = device.model_dump(mode="json", by_alias=True)
    assert data == {
        "driver": "wia",
        "id": "1",
        "name": "Scanner",
        "iconUri": "icon://scanner",
        "connectionUri": "usb://scanner",
    }


def test_scan_device_default_uris_are_none() -> None:
    device = ScanDevice(driver=Driver.WIA, id="1", name="Scanner")
    assert device.icon_uri is None
    assert device.connection_uri is None


def test_scan_device_invalid_driver_raises() -> None:
    with pytest.raises(ValidationError):
        ScanDevice(driver="unknown", id="1", name="Scanner")


def test_scan_device_equality() -> None:
    a = ScanDevice(driver=Driver.WIA, id="1", name="Scanner")
    b = ScanDevice(driver=Driver.WIA, id="1", name="Scanner")
    c = ScanDevice(driver=Driver.TWAIN, id="1", name="Scanner")

    assert a == b
    assert a != c


def test_custom_page_size_str_and_repr() -> None:
    page = CustomPageSize(width=210.0, height=297.0, unit=PageSizeUnit.MM)

    assert str(page) == "210.0x297.0mm"
    assert repr(page) == "210.0x297.0mm"


def test_custom_page_size_with_decimal_values() -> None:
    page = CustomPageSize(width=Decimal("8.5"), height=Decimal("11"), unit=PageSizeUnit.INCH)

    assert str(page) == "8.5x11.0in"


def test_scan_area_size_is_custom_page_size() -> None:
    area = ScanAreaSize(width=210, height=297, unit=PageSizeUnit.MM)

    assert isinstance(area, CustomPageSize)
    assert str(area) == "210.0x297.0mm"


@pytest.mark.parametrize(
    ("page_size", "expected"),
    [
        (PageSizeName.A4, "A4"),
        (CustomPageSize(width=210, height=297, unit=PageSizeUnit.MM), "210.0x297.0mm"),
        (CustomPageSize(width=8.5, height=11, unit=PageSizeUnit.INCH), "8.5x11.0in"),
        (CustomPageSize(width=10, height=20, unit=PageSizeUnit.CM), "10.0x20.0cm"),
    ],
)
def test_page_size_serialization(page_size, expected: str) -> None:
    options = ScanOptions(page_size=page_size)
    data = options.model_dump(mode="json", by_alias=True)
    assert data["pageSize"] == expected


def test_source_capabilities_dpi_properties() -> None:
    source = SourceCapabilities(
        type=PaperSource.FLATBED,
        resolutions=[150, 300, 1200],
    )

    assert source.min_dpi == 150
    assert source.max_dpi == 1200


def test_source_capabilities_empty_resolutions_raise() -> None:
    source = SourceCapabilities(type=PaperSource.FLATBED)

    with pytest.raises(ValueError):
        _ = source.min_dpi

    with pytest.raises(ValueError):
        _ = source.max_dpi


def test_scanner_capabilities_paper_sources() -> None:
    flatbed = SourceCapabilities(type=PaperSource.FLATBED)
    feeder = SourceCapabilities(type=PaperSource.FEEDER)

    caps = ScannerCapabilities(metadata=CapsMetadata(), flatbed=flatbed, feeder=feeder)

    assert caps.paper_sources == [flatbed, feeder]


def test_scanner_capabilities_no_paper_sources() -> None:
    caps = ScannerCapabilities(metadata=CapsMetadata())
    assert caps.paper_sources == []


def test_caps_metadata_serialization() -> None:
    metadata = CapsMetadata(
        driver_subtype="wia",
        icon_uri="icon://scanner",
        manufacturer="Canon",
        model="CanoScan",
        serial_number="12345",
    )

    data = metadata.model_dump(mode="json", by_alias=True)
    assert data == {
        "driverSubtype": "wia",
        "iconUri": "icon://scanner",
        "manufacturer": "Canon",
        "model": "CanoScan",
        "serialNumber": "12345",
    }


def test_scan_options_merge_preserves_unset_values() -> None:
    original = ScanOptions(
        dpi=300,
        color_mode=ColorMode.COLOR,
        paper_source=PaperSource.FLATBED,
        brightness=10,
    )

    merged = original.merge(
        dpi=UNSET_VALUE,
        color_mode=ColorMode.GRAY,
        brightness=UNSET_VALUE,
    )

    assert merged.dpi == 300
    assert merged.color_mode is ColorMode.GRAY
    assert merged.paper_source is PaperSource.FLATBED
    assert merged.brightness == 10


def test_scan_options_merge_can_override_falsey_values() -> None:
    original = ScanOptions(
        brightness=20,
        contrast=20,
        brightness_contrast_after_scan=True,
        use_native_ui=True,
    )

    merged = original.merge(
        brightness=0,
        contrast=0,
        brightness_contrast_after_scan=False,
        use_native_ui=False,
    )

    assert merged.brightness == 0
    assert merged.contrast == 0
    assert merged.brightness_contrast_after_scan is False
    assert merged.use_native_ui is False


def test_scan_options_merge_all_unset_returns_unchanged() -> None:
    original = ScanOptions(dpi=300, brightness=15)
    merged = original.merge(
        dpi=UNSET_VALUE,
        brightness=UNSET_VALUE,
        contrast=UNSET_VALUE,
        color_mode=UNSET_VALUE,
        paper_source=UNSET_VALUE,
        page_size=UNSET_VALUE,
        brightness_contrast_after_scan=UNSET_VALUE,
        use_native_ui=UNSET_VALUE,
    )

    assert merged.dpi == 300
    assert merged.brightness == 15
    assert merged.contrast == 0


def test_scan_options_serialization_includes_all_fields() -> None:
    options = ScanOptions(dpi=300)
    data = options.model_dump(mode="json", by_alias=True)

    assert data == {
        "dpi": 300,
        "colorMode": None,
        "paperSource": None,
        "pageSize": None,
        "brightness": 0,
        "contrast": 0,
        "brightnessContrastAfterScan": False,
        "useNativeUI": False,
    }


def test_scan_options_full_serialization() -> None:
    options = ScanOptions(
        dpi=300,
        color_mode=ColorMode.GRAY,
        paper_source=PaperSource.FLATBED,
        page_size=PageSizeName.A4,
        brightness=15,
        contrast=-5,
        brightness_contrast_after_scan=True,
        use_native_ui=True,
    )

    data = json.loads(options.model_dump_json(by_alias=True))

    assert data == {
        "dpi": 300,
        "colorMode": "gray",
        "paperSource": "flatbed",
        "pageSize": "A4",
        "brightness": 15,
        "contrast": -5,
        "brightnessContrastAfterScan": True,
        "useNativeUI": True,
    }


def test_scan_options_deserialization_from_json() -> None:
    data = {
        "dpi": 300,
        "colorMode": "gray",
        "paperSource": "flatbed",
        "pageSize": "A4",
        "brightness": 10,
        "contrast": 5,
        "brightnessContrastAfterScan": True,
        "useNativeUI": False,
    }

    options = ScanOptions.model_validate(data)

    assert options.dpi == 300
    assert options.color_mode is ColorMode.GRAY
    assert options.paper_source is PaperSource.FLATBED
    assert options.page_size is PageSizeName.A4
    assert options.brightness == 10
    assert options.contrast == 5
    assert options.brightness_contrast_after_scan is True
    assert options.use_native_ui is False


def test_dpi_type_alias() -> None:
    value: DPI = 300
    assert isinstance(value, int)
