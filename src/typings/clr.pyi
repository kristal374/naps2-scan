from typing import Any

def AddReference(
    name: str,
    *args: Any,
    **kwargs: Any
) -> Any: ...


def AddReferenceToFile(*names: str) -> None: ...


def AddReferenceToFileAndPath(path: str) -> None: ...


def GetClrType(python_type: type) -> Any: ...
