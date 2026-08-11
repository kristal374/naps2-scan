from collections.abc import Callable
from typing import Any, TypedDict

class Devices(TypedDict):
    Driver: str
    Id: str
    Name: str
    IconUri: str | None
    ConnectionUri: str | None

class Results[T]:
    def GetResult(self) -> T: ...

class Awaitable[T]:
    def GetAwaiter(self) -> Results[T]: ...
    def Wait(self) -> None: ...

class Bridge:
    @staticmethod
    def Initialize() -> None: ...
    @staticmethod
    def Shutdown() -> None: ...
    @staticmethod
    def GetDevicesAsync(driver: Any, timeout: int) -> Awaitable[str]: ...
    @staticmethod
    def GetCapabilitiesAsync(device: Any) -> Awaitable[str]: ...
    @staticmethod
    def ScanAsync(
        options_json: str,
        on_scan_start: Callable[[], None] | None,
        on_scan_end: Callable[[], None] | None,
        on_page_start: Callable[[int], None] | None,
        on_page_end: Callable[[int], None] | None,
        processed_new_image: Callable[[bytes, int, int, str], None],
        on_page_progress: Callable[[int, float], None] | None,
        cancel_token: Any,
    ) -> Awaitable[None]: ...
