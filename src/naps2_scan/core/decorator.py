from __future__ import annotations

import asyncio
import functools
from typing import Callable, Coroutine, Any, ParamSpec, TypeVar

from .exception import wrap_scan_exception

P = ParamSpec("P")
T = TypeVar("T")


def dotnet_async(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as exc:
            raise wrap_scan_exception(exc) from exc

    return wrapper
