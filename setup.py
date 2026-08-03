from __future__ import annotations

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
from setuptools.logging import configure

logger = logging.getLogger(__name__)
configure()

ROOT = Path(__file__).resolve().parent
NATIVE_DIR = ROOT / "src" / "naps2_bridge" / "native"
NATIVE_PROJECT = NATIVE_DIR / "NAPS2Bridge.csproj"
NATIVE_BIN_DIRNAME = "native_bin"

CONFIGURATION = "Release"
TARGET_FRAMEWORK_DEFAULT = "net8.0"
TARGET_FRAMEWORK_MACOS = os.environ.get("NAPS2_BRIDGE_MACOS_TFM", "net8.0-macos13.0")

RID_TABLE = {
    "win32": {"default": "win-x64", "arm": "win-arm64"},
    "linux": {"default": "linux-x64", "arm": "linux-arm64"},
    "darwin": {"default": "osx-x64", "arm": "osx-arm64"},
}
ARM_MACHINES = {"arm64", "aarch64"}


class NativeBuildError(RuntimeError):
    """Raised when the native (C#) build step fails."""


def resolve_rid() -> str:
    override = os.environ.get("NAPS2_BRIDGE_RID")
    if override:
        logger.info("Using RID from NAPS2_BRIDGE_RID: %s", override)
        return override

    platform_rids = RID_TABLE.get(sys.platform)
    if platform_rids is None:
        raise NativeBuildError(
            f"Unsupported platform for native build: {sys.platform!r}. "
            "Set NAPS2_BRIDGE_RID to override auto-detection."
        )

    is_arm = platform.machine().lower() in ARM_MACHINES
    return platform_rids["arm" if is_arm else "default"]


def find_dotnet() -> str:
    override = os.environ.get("NAPS2_BRIDGE_DOTNET")
    if override:
        if not Path(override).exists():
            raise NativeBuildError(
                f"NAPS2_BRIDGE_DOTNET points to a missing file: {override}"
            )
        return override

    dotnet = shutil.which("dotnet")
    if dotnet is None:
        raise NativeBuildError(
            "The 'dotnet' executable was not found on PATH.\n"
            "Install the .NET 8 SDK from https://dotnet.microsoft.com/download "
            "(the SDK is required to build, not just the runtime), or set "
            "NAPS2_BRIDGE_DOTNET to its full path.\n"
            "To skip the native build entirely, set NAPS2_BRIDGE_SKIP_NATIVE_BUILD=1."
        )
    return dotnet


def target_framework_for(rid: str) -> str:
    if rid.startswith("osx"):
        return TARGET_FRAMEWORK_MACOS
    return TARGET_FRAMEWORK_DEFAULT


def ensure_macos_build_host(rid: str) -> None:
    if rid.startswith("osx") and sys.platform != "darwin":
        raise NativeBuildError(
            f"Cannot build native binaries for {rid} on {sys.platform!r}. "
            f"macOS builds require TFM {TARGET_FRAMEWORK_MACOS} (Driver.Apple) "
            "and must be run on a macOS host with the .NET 8 SDK and macOS "
            "workload installed (dotnet workload install macOS)."
        )


def publish_dir_for(rid: str) -> Path:
    tfm = target_framework_for(rid)
    return NATIVE_DIR / "bin" / CONFIGURATION / tfm / rid / "publish"


def publish_native(rid: str, dotnet_exe: str) -> Path:
    if not NATIVE_PROJECT.exists():
        raise NativeBuildError(f"Native project not found: {NATIVE_PROJECT}")

    ensure_macos_build_host(rid)

    out_dir = publish_dir_for(rid)
    if out_dir.exists() and os.environ.get("NAPS2_BRIDGE_FORCE_REBUILD") != "1":
        logger.info(
            "Reusing existing native build for %s at %s "
            "(set NAPS2_BRIDGE_FORCE_REBUILD=1 to force a rebuild)",
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
    logger.info("Building native bridge for %s (TFM %s): %s", rid, tfm, " ".join(args))

    result = subprocess.run(args, cwd=ROOT)
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
    dest_dir = build_lib / "naps2_bridge" / "bridge" / NATIVE_BIN_DIRNAME

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(publish_dir, dest_dir)

    file_count = sum(1 for path in dest_dir.rglob("*") if path.is_file())
    logger.info("Copied %d files into %s", file_count, dest_dir)


def _publish_failure_message(rid: str, tfm: str, exit_code: int) -> str:
    macos_hint = ""
    if rid.startswith("osx"):
        macos_hint = (
            f"\nmacOS builds require TFM {TARGET_FRAMEWORK_MACOS} (Driver.Apple) and "
            "must be run on macOS with the macOS .NET workload installed "
            "(dotnet workload install macOS)."
        )
    return (
        f"`dotnet publish` failed with exit code {exit_code}. "
        "See the dotnet/NuGet/MSBuild output above for the actual cause "
        "(common culprits: missing .NET 8 SDK, no network access to "
        "NuGet, or a PackageReference that isn't compatible with this "
        f"RID: {rid}, TFM: {tfm}).{macos_hint}"
    )


class BuildPyWithNative(build_py):
    def run(self) -> None:
        if os.environ.get("NAPS2_BRIDGE_SKIP_NATIVE_BUILD") == "1":
            logger.warning(
                "NAPS2_BRIDGE_SKIP_NATIVE_BUILD=1 set — skipping native build. "
                "The resulting package will NOT include native_bin and will "
                "fail at import time."
            )
            super().run()
            return

        publish_dir = publish_native(resolve_rid(), find_dotnet())
        super().run()
        sync_native_binaries(publish_dir, Path(self.build_lib).resolve())


class BdistWheelWithNative(bdist_wheel):
    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        python, _abi, plat = super().get_tag()
        return python, "none", plat


setup(
    cmdclass={
        "build_py": BuildPyWithNative,
        "bdist_wheel": BdistWheelWithNative,
    }
)
