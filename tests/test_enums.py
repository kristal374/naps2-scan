from __future__ import annotations

import pytest

from naps2_scan.enums import (
    ColorMode,
    Driver,
    PageSizeName,
    PageSizeUnit,
    PaperSource,
)


@pytest.mark.parametrize(
    ("enum_cls", "member", "expected_value", "expected_repr"),
    [
        (Driver, Driver.DEFAULT, "default", "DEFAULT"),
        (Driver, Driver.WIA, "wia", "WIA"),
        (Driver, Driver.TWAIN, "twain", "TWAIN"),
        (Driver, Driver.APPLE, "apple", "APPLE"),
        (Driver, Driver.SANE, "sane", "SANE"),
        (Driver, Driver.ESCL, "escl", "ESCL"),
        (ColorMode, ColorMode.COLOR, "color", "COLOR"),
        (ColorMode, ColorMode.GRAY, "gray", "GRAY"),
        (ColorMode, ColorMode.BW, "bw", "BW"),
        (PaperSource, PaperSource.DUPLEX, "duplex", "DUPLEX"),
        (PaperSource, PaperSource.FEEDER, "feeder", "FEEDER"),
        (PaperSource, PaperSource.FLATBED, "flatbed", "FLATBED"),
        (PageSizeUnit, PageSizeUnit.MM, "mm", "MM"),
        (PageSizeUnit, PageSizeUnit.CM, "cm", "CM"),
        (PageSizeUnit, PageSizeUnit.INCH, "in", "INCH"),
        (PageSizeName, PageSizeName.A3, "A3", "A3"),
        (PageSizeName, PageSizeName.A4, "A4", "A4"),
        (PageSizeName, PageSizeName.A5, "A5", "A5"),
        (PageSizeName, PageSizeName.B4, "B4", "B4"),
        (PageSizeName, PageSizeName.B5, "B5", "B5"),
        (PageSizeName, PageSizeName.LEGAL, "Legal", "Legal"),
        (PageSizeName, PageSizeName.LETTER, "Letter", "Letter"),
    ],
)
def test_enum_members(enum_cls, member, expected_value, expected_repr) -> None:
    assert member.value == expected_value
    assert repr(member) == expected_repr
    # Only PageSizeName overrides __str__; other enums use default enum str().
    if enum_cls is PageSizeName:
        assert str(member) == expected_repr
    else:
        assert str(member).endswith(f".{member.name}")
