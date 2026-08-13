from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.build_py import build_py
from setuptools.command.editable_wheel import editable_wheel
from setuptools.logging import configure

logger = logging.getLogger(__name__)
configure()

ROOT = Path(__file__).resolve().parent
NATIVE_DIR = ROOT / "src" / "naps2_scan" / "native"
NATIVE_PROJECT = NATIVE_DIR / "NAPS2Bridge.csproj"
NATIVE_BIN_DIRNAME = "native_bin"

CONFIGURATION = "Release"
TARGET_FRAMEWORK_DEFAULT = "net8.0"

RID_TABLE = {
    "win32": {"default": "win-x64", "arm": "win-arm64"},
    "linux": {"default": "linux-x64", "arm": "linux-arm64"},
    "darwin": {"default": "osx-x64", "arm": "osx-arm64"},
}
ARM_MACHINES = {"arm64", "aarch64"}


class NativeBuildError(RuntimeError):
    """Raised when the native (C#) build step fails."""


def resolve_rid() -> str:
    override = os.environ.get("NAPS2_SCAN_RID")
    if override:
        logger.info("Using RID from NAPS2_SCAN_RID: %s", override)
        return override

    platform_rids = RID_TABLE.get(sys.platform)
    if platform_rids is None:
        raise NativeBuildError(
            f"Unsupported platform for native build: {sys.platform!r}. "
            "Set NAPS2_SCAN_RID to override auto-detection."
        )

    is_arm = platform.machine().lower() in ARM_MACHINES
    return platform_rids["arm" if is_arm else "default"]


def find_dotnet() -> str:
    override = os.environ.get("NAPS2_SCAN_DOTNET")
    if override:
        if not Path(override).exists():
            raise NativeBuildError(
                f"NAPS2_SCAN_DOTNET points to a missing file: {override}"
            )
        return override

    dotnet = shutil.which("dotnet")
    if dotnet is None:
        raise NativeBuildError(
            "The 'dotnet' executable was not found on PATH.\n"
            "Install the .NET 8 SDK from https://dotnet.microsoft.com/download "
            "(the SDK is required to build, not just the runtime), or set "
            "NAPS2_SCAN_DOTNET to its full path.\n"
            "To skip the native build entirely, set NAPS2_SCAN_SKIP_NATIVE_BUILD=1."
        )
    return dotnet


def target_framework_for(rid: str) -> str:
    return TARGET_FRAMEWORK_DEFAULT


def publish_dir_for(rid: str) -> Path:
    tfm = target_framework_for(rid)
    return NATIVE_DIR / "bin" / CONFIGURATION / tfm / rid / "publish"


def publish_native(rid: str, dotnet_exe: str) -> Path:
    if not NATIVE_PROJECT.exists():
        raise NativeBuildError(f"Native project not found: {NATIVE_PROJECT}")

    out_dir = publish_dir_for(rid)
    if out_dir.exists() and os.environ.get("NAPS2_SCAN_FORCE_REBUILD") != "1":
        logger.info(
            "Reusing existing native build for %s at %s "
            "(set NAPS2_SCAN_FORCE_REBUILD=1 to force a rebuild)",
            rid,
            out_dir,
        )
        return out_dir

    tfm = target_framework_for(rid)
    args = [
        dotnet_exe,
        "publish",
        str(NATIVE_PROJECT),
        "-c", CONFIGURATION,
        "-r", rid,
        "-f", tfm,
        "--self-contained", "false",
        "/p:PublishSingleFile=false",
        "/p:PublishReadyToRun=false",
        "/nologo",
    ]
    logger.info("Building native core for %s (TFM %s): %s", rid, tfm, " ".join(args))

    result = subprocess.run(args, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise NativeBuildError(_publish_failure_message(rid, tfm, result.returncode))

    if not out_dir.exists():
        raise NativeBuildError(
            "dotnet publish reported success but the expected output "
            f"directory is missing: {out_dir}"
        )

    logger.info("Native build finished: %s", out_dir)
    return out_dir


def sync_native_binaries(publish_dir: Path, build_lib: Path) -> None:
    dest_dir = build_lib / "naps2_scan" / "core" / NATIVE_BIN_DIRNAME

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(publish_dir, dest_dir)

    file_count = sum(1 for path in dest_dir.rglob("*") if path.is_file())
    logger.info("Copied %d files into %s", file_count, dest_dir)


def create_config(build_lib: Path) -> None:
    dest_dir = build_lib / "naps2_scan" / "core" / NATIVE_BIN_DIRNAME

    if not dest_dir.exists():
        raise RuntimeError("Destination directory is missing.")

    # NAPS2Bridge is built for .NET 8.0. Generate a minimal
    # runtime config so pythonnet can locate the shared runtime.
    config = {
        "runtimeOptions": {
            "tfm": "net8.0",
            "framework": {
                "name": "Microsoft.NETCore.App",
                "version": "8.0.0"
            },
            "rollForward": "LatestMajor"
        }
    }
    config_path = dest_dir / "NAPS2Bridge.runtimeconfig.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _publish_failure_message(rid: str, tfm: str, exit_code: int) -> str:
    return (
        f"`dotnet publish` failed with exit code {exit_code}. "
        "See the dotnet/NuGet/MSBuild output above for the actual cause "
        "(common culprits: missing .NET 8 SDK, no network access to "
        "NuGet, or a PackageReference that isn't compatible with this "
        f"RID: {rid}, TFM: {tfm})."
    )


class BuildPyWithNative(build_py):
    def run(self) -> None:
        if os.environ.get("NAPS2_SCAN_SKIP_NATIVE_BUILD") == "1":
            logger.warning(
                "NAPS2_SCAN_SKIP_NATIVE_BUILD=1 set — skipping native build. "
                "The resulting package will NOT include native_bin and will "
                "fail at import time."
            )
            super().run()
            return

        publish_dir = publish_native(resolve_rid(), find_dotnet())
        super().run()
        dest_dir = Path(self.build_lib).resolve()
        sync_native_binaries(publish_dir, dest_dir)
        create_config(dest_dir)


class BdistWheelWithNative(bdist_wheel):
    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        _python, _abi, plat = super().get_tag()
        target_plat = {
            "win-x64": "win_amd64",
            "win-arm64": "win_arm64",
            "linux-x64": "manylinux_2_17_x86_64",
            "linux-arm64": "manylinux_2_17_aarch64",
            "osx-x64": "macosx_10_15_x86_64",
            "osx-arm64": "macosx_11_0_arm64",
        }.get(resolve_rid(), plat)
        return "py3", "none", target_plat


class EditableWheelWithNative(editable_wheel):
    def run(self) -> None:
        if os.environ.get("NAPS2_SCAN_SKIP_NATIVE_BUILD") == "1":
            logger.warning(
                "NAPS2_SCAN_SKIP_NATIVE_BUILD=1 set — skipping native build. "
                "The package will fail at import time without native_bin."
            )
            super().run()
            return

        publish_dir = publish_native(resolve_rid(), find_dotnet())
        # Editable installs reference the source tree, so the binaries
        # must live next to the source package, not in build_lib.
        src_root = ROOT / "src"
        sync_native_binaries(publish_dir, src_root)
        create_config(src_root)
        super().run()


setup(
    cmdclass={
        "build_py": BuildPyWithNative,
        "bdist_wheel": BdistWheelWithNative,
        "editable_wheel": EditableWheelWithNative,
    }
)
