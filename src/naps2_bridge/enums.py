from enum import Enum


class Driver(Enum):
    DEFAULT = "default"
    WIA = "wia"
    TWAIN = "twain"
    APPLE = "apple"
    SANE = "sane"
    ESCL = "escl"

    def __repr__(self):
        return self.value.upper()


class ColorMode(Enum):
    COLOR = "color"
    GRAY = "gray"
    BW = "bw"


class PaperSource(Enum):
    DUPLEX = "duplex"
    FEEDER = "feeder"
    FLATBED = "flatbed"


class PixelFormat(Enum):
    BW1 = "bw1"
    GRAY8 = "gray8"
    RGB24 = "rgb24"
    RGBA32 = "rgba32"


class ImageFormat(Enum):
    PNG = "png"
    JPEG = "jpeg"


class PageSizeUnit(Enum):
    MM = "mm"
    CM = "cm"
    INCH = "in"


class PageSizeName(Enum):
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"

    B4 = "B4"
    B5 = "B5"

    LEGAL = "Legal"
    LETTER = "Letter"
