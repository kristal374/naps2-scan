"""Decorator for wrapping blocking .NET calls into async-safe coroutines.

The :func:`dotnet_async` decorator offloads a synchronous function to a
thread pool and wraps any .NET exceptions into their Python equivalents.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Coroutine

from .exception import wrap_scan_exception


def dotnet_async[**P, T](
    func: Callable[P, T],
) -> Callable[P, Coroutine[None, None, T]]:
    """Wrap a blocking .NET-API function so it can be awaited from asyncio.

    The wrapped function runs via :func:`asyncio.to_thread`.  If it raises
    a .NET exception, the exception is converted into a corresponding
    :class:`~naps2_scan.ScannerError` subclass via
    :func:`~naps2_scan.core.exception.wrap_scan_exception`.

    Args:
        func: A synchronous callable that may raise .NET exceptions.

    Returns:
        An async callable with the same signature.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as exc:
            raise wrap_scan_exception(exc) from exc

    return wrapper
