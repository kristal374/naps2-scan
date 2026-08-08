from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import List, Optional, Union, TypeVar, TypeAlias, TypedDict, Unpack, Protocol, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ScannedImage
    from .enums import ColorMode, Driver, PageSizeName, PageSizeUnit, PaperSource

DPI = int
UNSET_VALUE = object()

ARGUMENTS = TypeVar("ARGUMENTS")
OptionalArg: TypeAlias = ARGUMENTS | object

StartCallback = Callable[[], None]
PageStartCallback = Callable[[int], None]


class ProgressCallback(Protocol):
    def __call__(self, page_number: int, progress: float) -> None: ...


class PageCallback(Protocol):
    def __call__(self, page_number: int, image: ScannedImage) -> None: ...


@dataclass(frozen=True)
class ScanDevice:
    driver: Driver

    id: str
    name: str
    icon_uri: Optional[str] = None
    connection_uri: Optional[str] = None


@dataclass(frozen=True)
class CustomPageSize:
    width: Decimal
    height: Decimal
    unit: PageSizeUnit


@dataclass(frozen=True)
class ScanAreaSize(CustomPageSize):
    def __repr__(self):
        return f"{self.width}x{self.height}{self.unit.value}"


PageSize = Union[PageSizeName, CustomPageSize]


@dataclass(frozen=True)
class SourceCapabilities:
    type: PaperSource
    resolutions: List[DPI] = field(default_factory=list)
    color_modes: List[ColorMode] = field(default_factory=list)
    max_scan_area: Optional[ScanAreaSize] = None

    @property
    def min_dpi(self) -> DPI:
        return min(self.resolutions)

    @property
    def max_dpi(self) -> DPI:
        return max(self.resolutions)


@dataclass(frozen=True)
class CapsMetadata:
    driver_subtype: Optional[str] = None
    icon_uri: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


@dataclass(frozen=True)
class ScannerCapabilities:
    metadata: CapsMetadata

    flatbed: Optional[SourceCapabilities] = None
    feeder: Optional[SourceCapabilities] = None
    duplex: Optional[SourceCapabilities] = None


    @property
    def paper_sources(self) -> list[SourceCapabilities]:
        return [x for x in (self.flatbed, self.feeder, self.duplex) if x is not None]


class ScanOptionsDict(TypedDict, total=False):
    dpi: Optional[int]
    color_mode: Optional[ColorMode]
    paper_source: Optional[PaperSource]
    page_size: Optional[PageSize]
    brightness: int
    contrast: int
    brightness_contrast_after_scan: bool
    use_native_ui: bool


@dataclass
class ScanOptions:
    dpi: Optional[int] = None
    color_mode: Optional[ColorMode] = None
    paper_source: Optional[PaperSource] = None
    page_size: Optional[PageSize] = None
    brightness: int = 0
    contrast: int = 0
    brightness_contrast_after_scan: bool = False
    use_native_ui: bool = False

    def merge(self, **kwargs: Unpack[ScanOptionsDict]) -> ScanOptions:
        return replace(self, **{k: v for k, v in kwargs.items() if v is not UNSET_VALUE})
