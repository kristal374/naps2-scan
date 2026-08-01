"""Image result types for scanned pages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from .enums import ColorMode, PixelFormat


class Image(ABC):
    """Abstract encoded or raw scanned image."""

    @property
    @abstractmethod
    def width(self) -> int:
        """Image width in pixels."""

    @property
    @abstractmethod
    def height(self) -> int:
        """Image height in pixels."""

    @property
    @abstractmethod
    def dpi(self) -> float:
        """Horizontal/vertical DPI (assumes square pixels)."""

    @property
    @abstractmethod
    def color_mode(self) -> ColorMode:
        """Color mode of the image."""

    @property
    @abstractmethod
    def page_index(self) -> int:
        """Zero-based page index within the scan session."""

    @property
    @abstractmethod
    def data(self) -> Optional[bytes]:
        """Encoded bytes for PNG/JPEG; ``None`` for raw scanned images."""

    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Save image data to a file path."""


class ScannedImage(Image):
    """Raw image produced by the scanner."""

    def __init__(
        self,
        width: int,
        height: int,
        dpi: float,
        color_mode: ColorMode,
        page_index: int,
    ) -> None:
        self._width = width
        self._height = height
        self._dpi = dpi
        self._color_mode = color_mode
        self._page_index = page_index

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def dpi(self) -> float:
        return self._dpi

    @property
    def color_mode(self) -> ColorMode:
        return self._color_mode

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def data(self) -> None:
        return None

    def save(self, path: Union[str, Path]) -> None:
        raise NotImplementedError(
            "ScannedImage cannot be saved directly; encode it with to_png() or to_jpeg() first."
        )

    def to_bytes(self, pixel_format: PixelFormat = PixelFormat.RGB24) -> bytes:
        """Return raw pixel bytes in the requested format."""
        raise NotImplementedError

    def to_png(self) -> PngImage:
        """Encode as PNG."""
        raise NotImplementedError

    def to_jpeg(self, quality: int = 85) -> JpegImage:
        """Encode as JPEG."""
        raise NotImplementedError


class PngImage(Image):
    """PNG-encoded image."""

    def __init__(
        self,
        data: bytes,
        width: int,
        height: int,
        dpi: float,
        color_mode: ColorMode,
        page_index: int,
    ) -> None:
        self._data = data
        self._width = width
        self._height = height
        self._dpi = dpi
        self._color_mode = color_mode
        self._page_index = page_index

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def dpi(self) -> float:
        return self._dpi

    @property
    def color_mode(self) -> ColorMode:
        return self._color_mode

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def data(self) -> bytes:
        return self._data

    def save(self, path: Union[str, Path]) -> None:
        Path(path).write_bytes(self._data)


class JpegImage(Image):
    """JPEG-encoded image."""

    def __init__(
        self,
        data: bytes,
        width: int,
        height: int,
        dpi: float,
        color_mode: ColorMode,
        page_index: int,
    ) -> None:
        self._data = data
        self._width = width
        self._height = height
        self._dpi = dpi
        self._color_mode = color_mode
        self._page_index = page_index

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def dpi(self) -> float:
        return self._dpi

    @property
    def color_mode(self) -> ColorMode:
        return self._color_mode

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def data(self) -> bytes:
        return self._data

    def save(self, path: Union[str, Path]) -> None:
        Path(path).write_bytes(self._data)
