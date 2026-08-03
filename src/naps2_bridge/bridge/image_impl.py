from __future__ import annotations

from .interop import to_pixel_format
from naps2_bridge.enums import PixelFormat
from naps2_bridge.images import ScannedImage, ScannedImageMetadata


class ScannedImageRuntime(ScannedImage):
    def __init__(self, metadata: ScannedImageMetadata, pixel_format: PixelFormat, data: bytes) -> None:
        super().__init__(metadata, pixel_format, data)

    def convert(self, pixel_format: PixelFormat = PixelFormat.RGB24) -> ScannedImage:
        raise NotImplementedError

    def to_png(self) -> bytes:
        raise NotImplementedError

    def to_jpeg(self) -> bytes:
        raise NotImplementedError
