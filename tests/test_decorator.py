from __future__ import annotations

import asyncio

import pytest

from naps2_scan.core.decorator import dotnet_async
from naps2_scan.exceptions import DeviceNotFoundError, ScanCancelledError


def test_dotnet_async_wraps_exception() -> None:
    @dotnet_async
    def failing():
        raise type("DeviceNotFoundException", (Exception,), {})("missing")

    with pytest.raises(DeviceNotFoundError, match="missing"):
        asyncio.run(failing())


def test_dotnet_async_returns_result() -> None:
    @dotnet_async
    def succeeding() -> str:
        return "ok"

    result = asyncio.run(succeeding())

    assert result == "ok"


def test_dotnet_async_wraps_cancellation() -> None:
    @dotnet_async
    def cancelled():
        raise type("OperationCanceledException", (Exception,), {})("cancelled")

    with pytest.raises(ScanCancelledError, match="cancelled"):
        asyncio.run(cancelled())
