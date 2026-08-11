from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Coroutine

from .exception import wrap_scan_exception


def dotnet_async[**P, T](
    func: Callable[P, T],
) -> Callable[P, Coroutine[None, None, T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as exc:
            raise wrap_scan_exception(exc) from exc

    return wrapper
