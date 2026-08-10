from typing import Any, TypedDict, Callable

from typing import Optional


class Devices(TypedDict):
    Driver: str
    Id: str
    Name: Optional[str]
    IconUri: Optional[str]
    ConnectionUri: Optional[str]


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
    def GetDevicesAsync(driver: Any) -> Awaitable[str]: ...

    @staticmethod
    def GetCapabilitiesAsync(device: Any) -> Awaitable[str]: ...

    @staticmethod
    def ScanAsync(
            options_json: str,
            on_scan_start: Optional[Callable[[], None]],
            on_scan_end: Optional[Callable[[], None]],
            on_page_start: Optional[Callable[[int], None]],
            on_page_end: Optional[Callable[[int], None]],
            processed_new_image: Callable[[bytes, int, int, str], None],
            on_page_progress: Optional[Callable[[int, float], None]],
            cancel_token: Any,
    ) -> Awaitable[None]: ...
