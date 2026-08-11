from __future__ import annotations

from typing import Union, TypeVar, TypeAlias, TypedDict, Unpack, Protocol, Callable

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from .enums import ColorMode, Driver, PageSizeUnit, PaperSource, PageSizeName

DPI = int
UNSET_VALUE = object()

ARGUMENTS = TypeVar("ARGUMENTS")
OptionalArg: TypeAlias = ARGUMENTS | object

StartCallback = Callable[[], None]
PageStartCallback = Callable[[int], None]


class ProgressCallback(Protocol):
    def __call__(self, page_number: int, progress: float) -> None: ...


class PageCallback(Protocol):
    def __call__(self, page_number: int) -> None: ...


class NAPS2BaseModel(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
    )


class ScanDevice(NAPS2BaseModel):
    driver: Driver
    id: str
    name: str

    icon_uri: str | None = Field(
        default=None,
        validation_alias="iconUri",
        serialization_alias="iconUri",
    )

    connection_uri: str | None = Field(
        default=None,
        validation_alias="connectionUri",
        serialization_alias="connectionUri",
    )

    @field_validator("driver", mode="before")
    @classmethod
    def parse_driver(cls, value):
        if isinstance(value, Driver):
            return value
        return Driver(value.lower())


class CustomPageSize(NAPS2BaseModel):
    width: float
    height: float
    unit: PageSizeUnit

    def __repr__(self) -> str:
        return f"{self.width}x{self.height}{self.unit.value}"

    def __str__(self) -> str:
        return repr(self)


class ScanAreaSize(CustomPageSize):
    pass


PageSize = Union[PageSizeName, CustomPageSize]


class SourceCapabilities(NAPS2BaseModel):
    type: PaperSource
    resolutions: list[DPI] = Field(default_factory=list)
    color_modes: list[ColorMode] = Field(
        default_factory=list,
        validation_alias="colorModes",
        serialization_alias="colorModes",
    )
    max_scan_area: ScanAreaSize | None = Field(
        default=None,
        validation_alias="maxScanArea",
        serialization_alias="maxScanArea",
    )

    @property
    def min_dpi(self) -> DPI:
        return min(self.resolutions)

    @property
    def max_dpi(self) -> DPI:
        return max(self.resolutions)


class CapsMetadata(NAPS2BaseModel):
    driver_subtype: str | None = Field(
        default=None,
        validation_alias="driverSubtype",
        serialization_alias="driverSubtype",
    )
    icon_uri: str | None = Field(
        default=None,
        validation_alias="iconUri",
        serialization_alias="iconUri",
    )
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = Field(
        default=None,
        validation_alias="serialNumber",
        serialization_alias="serialNumber",
    )


class ScannerCapabilities(NAPS2BaseModel):
    metadata: CapsMetadata

    flatbed: SourceCapabilities | None = None
    feeder: SourceCapabilities | None = None
    duplex: SourceCapabilities | None = None

    @property
    def paper_sources(self) -> list[SourceCapabilities]:
        return [source for source in (self.flatbed, self.feeder, self.duplex,) if source is not None]


class ScanOptionsDict(TypedDict, total=False):
    dpi: DPI | None | UNSET_VALUE
    color_mode: ColorMode | None | UNSET_VALUE
    paper_source: PaperSource | None | UNSET_VALUE
    page_size: PageSize | None | UNSET_VALUE
    brightness: int | UNSET_VALUE
    contrast: int | UNSET_VALUE
    brightness_contrast_after_scan: bool | UNSET_VALUE
    use_native_ui: bool | UNSET_VALUE


class ScanOptions(NAPS2BaseModel):
    dpi: DPI | None = None

    color_mode: ColorMode | None = Field(
        default=None,
        validation_alias="colorMode",
        serialization_alias="colorMode",
    )

    paper_source: PaperSource | None = Field(
        default=None,
        validation_alias="paperSource",
        serialization_alias="paperSource",
    )

    page_size: PageSize | None = Field(
        default=None,
        validation_alias="pageSize",
        serialization_alias="pageSize",
    )

    brightness: int = 0
    contrast: int = 0

    brightness_contrast_after_scan: bool = Field(
        default=False,
        validation_alias="brightnessContrastAfterScan",
        serialization_alias="brightnessContrastAfterScan",
    )

    use_native_ui: bool = Field(
        default=False,
        validation_alias="useNativeUI",
        serialization_alias="useNativeUI",
    )

    @field_serializer("page_size")
    def serialize_page_size(self, value: PageSize | None) -> str | None:
        return str(value) if value is not None else None

    def merge(self, **kwargs: Unpack[ScanOptionsDict]) -> ScanOptions:
        data = self.model_dump()
        data.update({
            key: value
            for key, value in kwargs.items()
            if value is not UNSET_VALUE
        })

        return type(self).model_validate(data)
