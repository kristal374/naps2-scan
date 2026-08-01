"""Data types used by naps2_bridge."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import List, Optional, Union, TypeVar, TypeAlias

from .enums import ColorMode, Driver, PageSizeName, PageSizeUnit, PaperSource

DPI = int
UNSET_VALUE = object()

ARGUMENTS = TypeVar("ARGUMENTS")
OptionalArg: TypeAlias = ARGUMENTS | type[UNSET_VALUE.__class__]


@dataclass(frozen=True)
class ScanDevice:
    """Discovered scanner device."""
    driver: Driver

    id: str
    name: str
    icon_uri: Optional[str] = None
    connection_uri: Optional[str] = None


@dataclass(frozen=True)
class CustomPageSize:
    """Custom page size with explicit dimensions."""

    width: Decimal
    height: Decimal
    unit: PageSizeUnit


@dataclass(frozen=True)
class ScanAreaSize(CustomPageSize):
    def __repr__(self):
        return f"{self.width}x{self.height}{self.unit}"


PageSize = Union[PageSizeName, CustomPageSize]


@dataclass(frozen=True)
class SourceCapabilities:
    type: PaperSource
    resolutions: List[DPI] = field(default_factory=list)
    color_modes: List[ColorMode] = field(default_factory=list)
    max_scan_area: Optional[ScanAreaSize] = None

    def min_dpi(self) -> DPI:
        return min(self.resolutions)

    def max_dpi(self) -> DPI:
        return max(self.resolutions)


@dataclass(frozen=True)
class ScannerCapabilities:
    """Capabilities reported by a connected scanner."""

    flatbed: Optional[SourceCapabilities] = None
    feeder: Optional[SourceCapabilities] = None

    @property
    def paper_sources(self) -> list[SourceCapabilities]:
        return [x for x in (self.flatbed, self.feeder) if x is not None]


@dataclass
class ScanOptions:
    """Settings for a single scan operation."""

    dpi: Optional[int] = None
    color_mode: Optional[ColorMode] = None
    paper_source: Optional[PaperSource] = None
    page_size: Optional[PageSize] = None
    brightness: int = 0
    contrast: int = 0
    brightness_contrast_after_scan: bool = False
    use_native_ui: bool = False

    def merge(self, **kwargs) -> "ScanOptions":
        """Return a new ScanOptions with fields overridden by kwargs."""
        return replace(self, **{k: v for k, v in kwargs.items() if v is not UNSET_VALUE})
