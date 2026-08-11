"""Public type definitions for naps2_scan.

Data models for devices, capabilities, and scan options.  All models
are Pydantic-based and support serialization/deserialization with
camelCase aliases matching the NAPS2 bridge JSON format.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypedDict, Unpack

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from .enums import ColorMode, Driver, PageSizeName, PageSizeUnit, PaperSource


class _Unset:
    """Sentinel value for distinguishing *not provided* from ``None``."""

    def __repr__(self) -> str:
        return "UNSET_VALUE"


UNSET_VALUE = _Unset()
"""Sentinel used for scan option keyword arguments.

Pass ``dpi=UNSET_VALUE`` to leave a parameter unchanged when calling
:meth:`ScanOptions.merge` or :meth:`Scanner.scan`.
"""

type OptionalArg[ARGUMENTS] = ARGUMENTS | _Unset
"""A value that was either explicitly provided or left unset."""

DPI = int
"""Type alias for dots-per-inch values."""

StartCallback = Callable[[], None]
"""Callback with no arguments, fired when a scan session starts or ends."""

PageCallback = Callable[[int], None]
"""Callback receiving a 1-based page number."""


class ProgressCallback(Protocol):
    def __call__(self, page_number: int, progress: float, /) -> None:
        """Callback for scan progress updates.

        Args:
            page_number: 1-based page index.
            progress: A float typically in ``[0...1]`` representing
                completion percentage.
        """


class NAPS2BaseModel(BaseModel):
    """Base Pydantic model with camelCase alias support."""

    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
    )


class ScanDevice(NAPS2BaseModel):
    """A discovered scanner device.

    Attributes:
        driver: The :class:`Driver` used to discover this device.
        id: Unique identifier string.
        name: Human-readable device name.
        icon_uri: Optional URI to a device icon.
        connection_uri: Optional connection URI (e.g. USB path).
    """

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
    def parse_driver(cls, value: Driver | str) -> Driver:
        """Accept both ``Driver`` enum and case-insensitive string."""
        if isinstance(value, Driver):
            return value
        return Driver(value.lower())


class CustomPageSize(NAPS2BaseModel):
    """A custom page size with explicit dimensions.

    Attributes:
        width: Page width in the given *unit*.
        height: Page height in the given *unit*.
        unit: Unit of measurement (:class:`PageSizeUnit`).

    Example:
        >>> CustomPageSize(width=210, height=297, unit=PageSizeUnit.MM)
    """

    width: float
    height: float
    unit: PageSizeUnit

    def __repr__(self) -> str:
        return f"{self.width}x{self.height}{self.unit.value}"

    def __str__(self) -> str:
        return repr(self)


class ScanAreaSize(CustomPageSize):
    """Maximum physical scan area of a device."""


PageSize = PageSizeName | CustomPageSize
"""Either a standard :class:`PageSizeName` or a :class:`CustomPageSize`."""


class SourceCapabilities(NAPS2BaseModel):
    """Capabilities of a single paper source (flatbed / feeder / duplex).

    Attributes:
        type: The paper source type.
        resolutions: Supported DPI values.
        color_modes: Supported color modes.
        max_scan_area: Maximum physical scan area, or ``None``.
    """

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
        """Minimum supported DPI."""
        return min(self.resolutions)

    @property
    def max_dpi(self) -> DPI:
        """Maximum supported DPI."""
        return max(self.resolutions)


class CapsMetadata(NAPS2BaseModel):
    """Metadata about a scanner device.

    Attributes:
        driver_subtype: Driver-specific subtype string.
        icon_uri: URI to a device icon.
        manufacturer: Manufacturer name.
        model: Model name.
        serial_number: Serial number.
    """

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
    """Full set of capabilities returned by a scanner.

    Attributes:
        metadata: Device metadata.
        flatbed: Flatbed source capabilities, or ``None`` if not available.
        feeder: Feeder source capabilities, or ``None``.
        duplex: Duplex source capabilities, or ``None``.
    """

    metadata: CapsMetadata

    flatbed: SourceCapabilities | None = None
    feeder: SourceCapabilities | None = None
    duplex: SourceCapabilities | None = None

    @property
    def paper_sources(self) -> list[SourceCapabilities]:
        """All available paper sources (non-``None``)."""
        return [
            source
            for source in (
                self.flatbed,
                self.feeder,
                self.duplex,
            )
            if source is not None
        ]


class ScanOptionsDict(TypedDict, total=False):
    """TypedDict for :meth:`ScanOptions.merge` keyword arguments."""

    dpi: OptionalArg[DPI | None]
    color_mode: OptionalArg[ColorMode | None]
    paper_source: OptionalArg[PaperSource | None]
    page_size: OptionalArg[PageSize | None]
    brightness: OptionalArg[int]
    contrast: OptionalArg[int]
    brightness_contrast_after_scan: OptionalArg[bool]
    use_native_ui: OptionalArg[bool]


class ScanOptions(NAPS2BaseModel):
    """Options for a scan operation.

    All fields are optional; the scanner will use device defaults for
    any field left as ``None``.

    Attributes:
        dpi: Resolution in DPI (``None`` = device default).
        color_mode: :class:`ColorMode`.
        paper_source: :class:`PaperSource`.
        page_size: Standard name or :class:`CustomPageSize`.
        brightness: Brightness adjustment.
        contrast: Contrast adjustment.
        brightness_contrast_after_scan: Apply after scan.
        use_native_ui: Show vendor's native UI dialog.
    """

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
        """Return a new ``ScanOptions`` with *kwargs* applied.

        Values set to :data:`UNSET_VALUE` are left unchanged from the
        original options.  Any other value (including ``None`` or ``0``)
        replaces the original.

        Example:
            >>> base = ScanOptions(dpi=300, brightness=10)
            >>> base.merge(brightness=0)
            ScanOptions(dpi=300, brightness=0)
        """
        data = self.model_dump()
        data.update(
            {key: value for key, value in kwargs.items() if value is not UNSET_VALUE}
        )
        return type(self).model_validate(data)
