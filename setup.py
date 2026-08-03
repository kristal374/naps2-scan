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

ROOT = Path(__file__).parent.resolve()
NATIVE_DIR = ROOT / "src" / "naps2_bridge" / "native"
NATIVE_PROJECT = NATIVE_DIR / "NAPS2Bridge.csproj"
NATIVE_BIN_DIRNAME = "native_bin"

CONFIGURATION = "Release"
TARGET_FRAMEWORK = "net8.0"

_RID_TABLE = {
    "win32": {"default": "win-x64", "arm": "win-arm64"},
    "linux": {"default": "linux-x64", "arm": "linux-arm64"},
    "darwin": {"default": "osx-x64", "arm": "osx-arm64"},
}
_ARM_MACHINES = {"arm64", "aarch64"}


class NativeBuildError(RuntimeError):
    """Raised when the native (C#) build step fails."""


def resolve_rid() -> str:
    override = os.environ.get("NAPS2_BRIDGE_RID")
    if override:
        logger.info("Using RID from NAPS2_BRIDGE_RID: %s", override)
        return override

    platform_rids = _RID_TABLE.get(sys.platform)
    if platform_rids is None:
        raise NativeBuildError(
            f"Unsupported platform for native build: {sys.platform!r}. "
            f"Set NAPS2_BRIDGE_RID to override auto-detection."
        )

    is_arm = platform.machine().lower() in _ARM_MACHINES
    return platform_rids["arm" if is_arm else "default"]


def find_dotnet() -> str:
    override = os.environ.get("NAPS2_BRIDGE_DOTNET")
    if override:
        if not Path(override).exists():
            raise NativeBuildError(f"NAPS2_BRIDGE_DOTNET points to a missing file: {override}")
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


def publish_dir_for(rid: str) -> Path:
    return NATIVE_DIR / "bin" / CONFIGURATION / TARGET_FRAMEWORK / rid / "publish"


def publish_native(rid: str, dotnet_exe: str) -> Path:
    if not NATIVE_PROJECT.exists():
        raise NativeBuildError(f"Native project not found: {NATIVE_PROJECT}")

    out_dir = publish_dir_for(rid)
    force = os.environ.get("NAPS2_BRIDGE_FORCE_REBUILD") == "1"
    if out_dir.exists() and not force:
        logger.info("Reusing existing native build for %s at %s (set "
                    "NAPS2_BRIDGE_FORCE_REBUILD=1 to force a rebuild)", rid, out_dir)
        return out_dir

    args = [
        dotnet_exe, "publish", str(NATIVE_PROJECT),
        "-c", CONFIGURATION,
        "-r", rid,
        "-f", TARGET_FRAMEWORK,
        "--self-contained", "false",
        "/p:PublishSingleFile=false",
        "/p:PublishReadyToRun=false",
        "/nologo",
    ]
    logger.info("Building native bridge for %s: %s", rid, " ".join(args))

    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        raise NativeBuildError(
            f"`dotnet publish` failed with exit code {result.returncode}. "
            "See the dotnet/NuGet/MSBuild output above for the actual cause "
            "(common culprits: missing .NET 8 SDK, no network access to "
            "NuGet, or a PackageReference that isn't compatible with this "
            f"RID: {rid})."
        )
    logger.info("Native build finished: %s", out_dir)

    if not out_dir.exists():
        raise NativeBuildError(
            f"dotnet publish reported success but the expected output "
            f"directory is missing: {out_dir}"
        )
    return out_dir


def sync_native_binaries(publish_dir: Path, build_lib: Path) -> None:
    dest_dir = build_lib / "naps2_bridge" / "bridge" / NATIVE_BIN_DIRNAME

    if dest_dir.exists():
        shutil.rmtree(dest_dir)  # avoid stale files from a previous RID
    shutil.copytree(publish_dir, dest_dir)

    logger.info("Copied %d entries into %s",
                sum(1 for _ in dest_dir.rglob("*") if _.is_file()), dest_dir)


class MyBuild(build_py):
    def run(self) -> None:
        if os.environ.get("NAPS2_BRIDGE_SKIP_NATIVE_BUILD") == "1":
            logger.warning(
                "NAPS2_BRIDGE_SKIP_NATIVE_BUILD=1 set — skipping native build. "
                "The resulting package will NOT include native_bin and will "
                "fail at import time."
            )
            super().run()
            return

        rid = resolve_rid()
        dotnet_exe = find_dotnet()
        publish_dir = publish_native(rid, dotnet_exe)

        super().run()

        build_lib = Path(self.build_lib).resolve()
        sync_native_binaries(publish_dir, build_lib)


class MyBdistWheel(bdist_wheel):
    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        python, _abi, plat = super().get_tag()
        return python, "none", plat


setup(
    cmdclass={
        "build_py": MyBuild,
        "bdist_wheel": MyBdistWheel
    },
)
