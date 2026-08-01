"""Exception types for naps2_bridge."""


class ScannerError(Exception):
    """Base class for all scanner-related errors."""


class DeviceOfflineError(ScannerError):
    """Raised when the selected device is offline or unreachable."""


class DeviceNotFoundError(ScannerError):
    """Raised when the requested device cannot be found."""


class ScanCancelledError(ScannerError):
    """Raised when a scan operation is cancelled by the caller."""


class ScanDriverError(ScannerError):
    """Raised for driver-specific scan failures (paper jam, feeder empty, etc.)."""


class ValidationError(ScannerError):
    """Raised when scan options fail validation against device capabilities."""


class UnsupportedPixelFormatError(ScannerError):
    """Raised when the requested pixel format cannot be produced."""
