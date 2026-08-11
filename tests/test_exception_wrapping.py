from __future__ import annotations

import pytest

from naps2_scan.core.exception import wrap_scan_exception
from naps2_scan.exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    ScanCancelledError,
    ScanDriverError,
    ScanFailedError,
    ScannerError,
    UnsupportedPixelFormatError,
    ValidationError,
)


def _make_exc(name: str, message: str):
    return type(name, (Exception,), {})(message)


@pytest.mark.parametrize(
    ("exc_name", "expected_type"),
    [
        ("OperationCanceledException", ScanCancelledError),
        ("TaskCanceledException", ScanCancelledError),
        ("DeviceNotFoundException", DeviceNotFoundError),
        ("DeviceOfflineException", DeviceOfflineError),
        ("DeviceBusyException", ScanDriverError),
        ("DeviceCommunicationException", ScanDriverError),
        ("DeviceCoverOpenException", ScanDriverError),
        ("DeviceFeederEmptyException", ScanDriverError),
        ("DevicePaperJamException", ScanDriverError),
        ("DeviceWarmingUpException", ScanDriverError),
        ("ScanDriverException", ScanDriverError),
        ("ScanDriverUnknownException", ScanDriverError),
        ("DriverNotSupportedException", ScanDriverError),
        ("NoDuplexSupportException", ScanDriverError),
        ("NoFeederSupportException", ScanDriverError),
        ("DeviceException", ScanDriverError),
        ("AlreadyHandledDriverException", ScanDriverError),
        ("ArgumentException", ValidationError),
        ("ArgumentNullException", ValidationError),
        ("ArgumentOutOfRangeException", ValidationError),
        ("InvalidOperationException", ValidationError),
    ],
)
def test_dotnet_exceptions_are_wrapped(exc_name: str, expected_type: type) -> None:
    exc = _make_exc(exc_name, "something went wrong")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, expected_type)
    assert str(wrapped) == "something went wrong"
    assert wrapped.__cause__ is exc


def test_cancellation_is_wrapped() -> None:
    exc = _make_exc("OperationCanceledException", "cancelled")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, ScanCancelledError)


def test_aggregate_with_cancellation_is_unwrapped_to_cancelled() -> None:
    cancel = _make_exc("TaskCanceledException", "cancelled")
    exc = type("AggregateException", (Exception,), {"InnerExceptions": [cancel]})(
        "aggregate"
    )
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, ScanCancelledError)


def test_aggregate_with_device_error_is_unwrapped() -> None:
    device = _make_exc("DeviceNotFoundException", "missing")
    exc = type("AggregateException", (Exception,), {"InnerExceptions": [device]})(
        "aggregate"
    )
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, DeviceNotFoundError)


def test_aggregate_with_mixed_cancellation_and_device_error_is_unwrapped() -> None:
    cancel = _make_exc("TaskCanceledException", "cancelled")
    device = _make_exc("DeviceNotFoundException", "missing")
    exc = type(
        "AggregateException", (Exception,), {"InnerExceptions": [cancel, device]}
    )("aggregate")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, DeviceNotFoundError)


def test_target_invocation_is_unwrapped() -> None:
    inner = _make_exc("DeviceOfflineException", "offline")
    exc = type("TargetInvocationException", (Exception,), {"InnerException": inner})(
        "wrapper"
    )
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, DeviceOfflineError)


def test_unknown_exception_becomes_scanner_error() -> None:
    exc = _make_exc("SomeRandomException", "random")
    wrapped = wrap_scan_exception(exc)

    assert type(wrapped) is ScannerError


def test_unsupported_pixel_format_is_recognized() -> None:
    exc = _make_exc("NotSupportedException", "Unsupported pixel format: RGBA64")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, UnsupportedPixelFormatError)


def test_not_supported_without_pixel_format_is_scanner_error() -> None:
    exc = _make_exc("NotSupportedException", "Something else is not supported")
    wrapped = wrap_scan_exception(exc)

    assert type(wrapped) is ScannerError


def test_scan_failed_exception_is_wrapped() -> None:
    exc = _make_exc("ScanFailedException", "scan failed")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, ScanFailedError)


def test_already_wrapped_scanner_error_is_returned_unchanged() -> None:
    exc = DeviceNotFoundError("already wrapped")
    wrapped = wrap_scan_exception(exc)

    assert wrapped is exc


def test_aggregate_with_empty_inner_exceptions_falls_through() -> None:
    exc = type("AggregateException", (Exception,), {"InnerExceptions": []})("empty")
    wrapped = wrap_scan_exception(exc)

    assert isinstance(wrapped, ScannerError)


def test_cyclic_inner_exception_chain_breaks_loop() -> None:
    a = type("OuterException", (Exception,), {})("outer")
    b = type("InnerException", (Exception,), {})("inner")
    a.InnerException = b
    b.InnerException = a

    # Should not hang; should break the cycle and return whatever exc is at that point.
    wrapped = wrap_scan_exception(a)

    assert isinstance(wrapped, ScannerError)


def test_inner_exceptions_chain_unwraps_multiple_levels() -> None:
    inner = _make_exc("DeviceNotFoundException", "missing")
    middle = type("MiddleException", (Exception,), {"InnerException": inner})("middle")
    outer = type("OuterException", (Exception,), {"InnerException": middle})("outer")

    wrapped = wrap_scan_exception(outer)

    assert isinstance(wrapped, DeviceNotFoundError)
    assert str(wrapped) == "missing"
