"""Smoke test: verifies all public API symbols are importable and consistent."""

from __future__ import annotations

import inspect

import naps2_scan


def test_public_api_symbols_exist() -> None:
    """Every name in __all__ must be importable from naps2_scan."""
    for name in naps2_scan.__all__:
        obj = getattr(naps2_scan, name, None)
        assert obj is not None, f"{name} is in __all__ but missing from module"


def test_public_api_no_extra_symbols() -> None:
    """Every public class/function in the module should be in __all__."""
    public_names = {
        name
        for name in dir(naps2_scan)
        if not name.startswith("_") and not inspect.ismodule(getattr(naps2_scan, name))
    }
    all_set = set(naps2_scan.__all__)
    missing = public_names - all_set
    assert not missing, f"Public symbols not in __all__: {missing}"


def test_scanner_class_signatures() -> None:
    """Sync Scanner and AsyncScanner must have matching method sets."""
    sync_methods = {
        name
        for name, _ in inspect.getmembers(naps2_scan.Scanner, inspect.isfunction)
        if not name.startswith("_")
    }
    async_methods = {
        name
        for name, _ in inspect.getmembers(naps2_scan.AsyncScanner, inspect.isfunction)
        if not name.startswith("_")
    }
    assert sync_methods == async_methods, (
        f"Method mismatch: sync={sync_methods}, async={async_methods}"
    )


def test_exception_hierarchy() -> None:
    """All exception types must inherit from ScannerError."""
    base = naps2_scan.ScannerError
    for name in naps2_scan.__all__:
        if name.endswith("Error"):
            exc = getattr(naps2_scan, name)
            if inspect.isclass(exc):
                assert issubclass(exc, base), (
                    f"{name} does not inherit from ScannerError"
                )


def test_scan_options_defaults() -> None:
    """ScanOptions must have sensible defaults."""
    opts = naps2_scan.ScanOptions()
    assert opts.dpi is None
    assert opts.color_mode is None
    assert opts.paper_source is None
    assert opts.brightness == 0
    assert opts.contrast == 0
    assert opts.brightness_contrast_after_scan is False
    assert opts.use_native_ui is False


def test_scan_options_merge_idempotent() -> None:
    """merge() with no args returns equivalent object."""
    from naps2_scan.types import UNSET_VALUE

    opts = naps2_scan.ScanOptions(
        dpi=300,
        color_mode=naps2_scan.ColorMode.COLOR,
        brightness=10,
    )
    merged = opts.merge(
        dpi=UNSET_VALUE,
        color_mode=UNSET_VALUE,
        brightness=UNSET_VALUE,
    )
    assert merged.dpi == opts.dpi
    assert merged.color_mode == opts.color_mode
    assert merged.brightness == opts.brightness


def test_type_re_exports() -> None:
    """Verify key types are available at top level."""
    assert naps2_scan.ScanDevice is not None
    assert naps2_scan.ScannerCapabilities is not None
    assert naps2_scan.SourceCapabilities is not None
    assert naps2_scan.CapsMetadata is not None
    assert naps2_scan.ScanAreaSize is not None
    assert naps2_scan.CustomPageSize is not None
    assert naps2_scan.PageSize is not None
    assert naps2_scan.DPI is int


def test_sync_async_list_devices_signatures() -> None:
    """list_devices and async_list_devices must accept the same params."""
    sig_sync = inspect.signature(naps2_scan.list_devices)
    sig_async = inspect.signature(naps2_scan.async_list_devices)
    assert list(sig_sync.parameters) == list(sig_async.parameters)


def test_version_present() -> None:
    """Package must expose __version__."""
    assert naps2_scan.__version__
    assert isinstance(naps2_scan.__version__, str)
