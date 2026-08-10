from __future__ import annotations

import asyncio
import functools
from typing import (
    Callable,
    ParamSpec,
    TypeVar, Coroutine, Any,
)

from ..exceptions import ScannerError

P = ParamSpec("P")
T = TypeVar("T")


def dotnet_async(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except BaseException as exc:
            raise wrap_scan_exception(exc) from exc

    return wrapper


def wrap_scan_exception(exc: BaseException) -> ScannerError:
    if isinstance(exc, ScannerError):
        return exc

    inner_exceptions = getattr(exc, "InnerExceptions", None)
    if inner_exceptions is not None:
        for inner in inner_exceptions:
            if type(inner).__name__ != "TaskCanceledException":
                exc = inner
                break

    wrapped: ScannerError

    exc_name = type(exc).__name__
    exc_description = str(exc)
    match exc_name:
        case _:
            wrapped = ScannerError(exc_description)
    wrapped.__cause__ = exc
    return wrapped
