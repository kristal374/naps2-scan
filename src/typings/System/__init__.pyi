from typing import Any

class AppDomain:
    CurrentDomain: AppDomain

    @staticmethod
    def SetData(name: str, value: Any) -> None: ...

class AppContext:
    @staticmethod
    def SetData(name: str, value: Any) -> None: ...
