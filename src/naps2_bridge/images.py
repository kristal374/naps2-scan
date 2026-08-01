from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .enums import ColorMode, PixelFormat
from .types import DPI

FilePath = os.PathLike[str] | str


@dataclass(frozen=True, slots=True)
class ScannedImageMetadata:
    width: int
    height: int
    dpi: DPI
    color_mode: ColorMode
    page_index: int


class ScannedImage:
    def __init__(
            self,
            metadata: ScannedImageMetadata,
            pixel_format: PixelFormat,
            data: bytes
    ) -> None:
        self._metadata = metadata
        self._pixel_format = pixel_format
        self._data = data

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def metadata(self) -> ScannedImageMetadata:
        return self._metadata

    def convert(self, pixel_format: PixelFormat = PixelFormat.RGB24) -> ScannedImage: ...

    def to_png(self) -> bytes:
        ...

    def to_jpeg(self, quality: int = 95) -> bytes:
        ...

    def save_as_png(self, path: FilePath) -> int:
        return self._save(path=path, payload=self.to_png())

    def save_as_jpg(self, path: FilePath) -> int:
        return self._save(path=path, payload=self.to_jpeg())

    @staticmethod
    def _save(path: FilePath, payload: bytes) -> int:
        return Path(path).write_bytes(payload)
