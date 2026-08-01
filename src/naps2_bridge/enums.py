"""Enumerations used by naps2_bridge."""

from enum import Enum
from typing import Literal


class Driver(Enum):
    """Scanner driver/protocol to use."""

    DEFAULT = "default"
    WIA = "wia"
    TWAIN = "twain"
    SANE = "sane"
    ESCL = "escl"
    APPLE = "apple"


class ColorMode(Enum):
    """Color mode for scanning."""

    COLOR = "color"
    GRAY = "gray"
    BW = "bw"


class PaperSource(Enum):
    """Physical paper source on the scanner."""

    FLATBED = "flatbed"
    FEEDER = "feeder"


class PixelFormat(Enum):
    """Raw pixel format for byte extraction."""

    BW1 = "bw1"
    GRAY8 = "gray8"
    RGB24 = "rgb24"
    RGBA32 = "rgba32"


class ImageFormat(Enum):
    """Encoded image format."""

    PNG = "png"
    JPEG = "jpeg"


class PageSizeUnit(Enum):
    """Unit of length for custom page sizes."""

    MM = "mm"
    CM = "cm"
    INCH = "inch"


class PageSizeName(Enum):
    """Well-known page size names."""

    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"
    A7 = "A7"

    B0 = "B0"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    B5 = "B5"
    
    LETTER = "Letter"
    LEGAL = "Legal"


# Convenience literals for type hints.
DriverLiteral = Literal[
    "default",
    "wia",
    "twain",
    "sane",
    "escl",
    "apple",
]
