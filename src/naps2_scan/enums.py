"""Enumeration types used throughout naps2_scan."""

from enum import Enum


class Driver(Enum):
    """Scanner driver / protocol.

    Attributes:
        DEFAULT: Auto-detect the best driver.
        WIA: Windows Image Acquisition.
        TWAIN: TWAIN driver.
        APPLE: Apple Image Capture (macOS).
        SANE: Scanner Access Now Easy (Linux).
        ESCL: eSCL network protocol.
    """

    DEFAULT = "default"
    WIA = "wia"
    TWAIN = "twain"
    APPLE = "apple"
    SANE = "sane"
    ESCL = "escl"

    def __repr__(self) -> str:
        return self.name


class ColorMode(Enum):
    """Color mode for scanning.

    Attributes:
        COLOR: Full color (RGB / RGBA).
        GRAY: Grayscale.
        BW: Black and white (1-bit).
    """

    COLOR = "color"
    GRAY = "gray"
    BW = "bw"

    def __repr__(self) -> str:
        return self.name


class PaperSource(Enum):
    """Physical paper source.

    Attributes:
        DUPLEX: Automatic duplex (both sides).
        FEEDER: Automatic document feeder.
        FLATBED: Flatbed glass.
    """

    DUPLEX = "duplex"
    FEEDER = "feeder"
    FLATBED = "flatbed"

    def __repr__(self) -> str:
        return self.name


class PageSizeUnit(Enum):
    """Unit of measurement for custom page sizes.

    Attributes:
        MM: Millimetres.
        CM: Centimetres.
        INCH: Inches.
    """

    MM = "mm"
    CM = "cm"
    INCH = "in"

    def __repr__(self) -> str:
        return self.name


class PageSizeName(Enum):
    """Standard page size names.

    Attributes:
        A3, A4, A5: ISO A-series.
        B4, B5: ISO B-series.
        LEGAL: US Legal.
        LETTER: US Letter.
    """

    A3 = "A3"
    A4 = "A4"
    A5 = "A5"

    B4 = "B4"
    B5 = "B5"

    LEGAL = "Legal"
    LETTER = "Letter"

    def __repr__(self) -> str:
        return self.value

    def __str__(self) -> str:
        return repr(self)
