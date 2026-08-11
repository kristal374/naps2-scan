from __future__ import annotations

from inspect import getmro

from ..exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    ScanCancelledError,
    ScanDriverError,
    ScanFailedError,
    ScannerError,
    UnsupportedPixelFormatError,
    ValidationError,
)

_CANCELLATION_NAMES = frozenset({
    "OperationCanceledException",
    "TaskCanceledException",
})

_DEVICE_NOT_FOUND_NAMES = frozenset({
    "DeviceNotFoundException",
})

_DEVICE_OFFLINE_NAMES = frozenset({
    "DeviceOfflineException",
})

_DRIVER_ERROR_NAMES = frozenset({
    "AlreadyHandledDriverException",
    "DeviceBusyException",
    "DeviceCommunicationException",
    "DeviceCoverOpenException",
    "DeviceException",
    "DeviceFeederEmptyException",
    "DevicePaperJamException",
    "DeviceWarmingUpException",
    "DriverNotSupportedException",
    "NoDuplexSupportException",
    "NoFeederSupportException",
    "ScanDriverException",
    "ScanDriverUnknownException",
})

_VALIDATION_ERROR_NAMES = frozenset({
    "ArgumentException",
    "ArgumentNullException",
    "ArgumentOutOfRangeException",
    "InvalidOperationException",
})

_UNSUPPORTED_ERROR_NAMES = frozenset({
    "NotSupportedException"
})

_SCAN_FAILED_NAMES = frozenset({"ScanFailedException", "ScanException"})


def _is_named(exc: Exception, names: frozenset[str]) -> bool:
    return any(cls.__name__ in names for cls in getmro(type(exc)))


def _unwrap_exception(exc: Exception) -> Exception:
    seen = set()
    while id(exc) not in seen:
        seen.add(id(exc))

        inner_exceptions: list[Exception] = list(getattr(exc, "InnerExceptions", None) or [])
        if inner_exceptions:
            non_cancelled = [e for e in inner_exceptions if not _is_named(e, _CANCELLATION_NAMES)]
            exc = non_cancelled[0] if non_cancelled else inner_exceptions[0]
            continue

        inner: Exception | None = getattr(exc, "InnerException", None)
        if inner is not None:
            exc = inner
            continue

        break
    return exc


def wrap_scan_exception(exc: Exception) -> ScannerError:
    if isinstance(exc, ScannerError):
        return exc

    original = exc
    exc = _unwrap_exception(exc)

    message = str(exc)

    if _is_named(exc, _CANCELLATION_NAMES):
        wrapped = ScanCancelledError(message)
    elif _is_named(exc, _DEVICE_NOT_FOUND_NAMES):
        wrapped = DeviceNotFoundError(message)
    elif _is_named(exc, _DEVICE_OFFLINE_NAMES):
        wrapped = DeviceOfflineError(message)
    elif _is_named(exc, _DRIVER_ERROR_NAMES):
        wrapped = ScanDriverError(message)
    elif _is_named(exc, _VALIDATION_ERROR_NAMES):
        wrapped = ValidationError(message)
    elif _is_named(exc, _UNSUPPORTED_ERROR_NAMES) and "pixel format" in message.lower():
        wrapped = UnsupportedPixelFormatError(message)
    elif _is_named(exc, _SCAN_FAILED_NAMES):
        wrapped = ScanFailedError(message)
    else:
        wrapped = ScannerError(message)

    wrapped.__cause__ = original
    return wrapped
