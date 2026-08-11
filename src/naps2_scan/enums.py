from enum import Enum


class Driver(Enum):
    DEFAULT = "default"
    WIA = "wia"
    TWAIN = "twain"
    APPLE = "apple"
    SANE = "sane"
    ESCL = "escl"

    def __repr__(self) -> str:
        return self.name


class ColorMode(Enum):
    COLOR = "color"
    GRAY = "gray"
    BW = "bw"

    def __repr__(self) -> str:
        return self.name


class PaperSource(Enum):
    DUPLEX = "duplex"
    FEEDER = "feeder"
    FLATBED = "flatbed"

    def __repr__(self) -> str:
        return self.name


class PageSizeUnit(Enum):
    MM = "mm"
    CM = "cm"
    INCH = "in"

    def __repr__(self) -> str:
        return self.name


class PageSizeName(Enum):
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
