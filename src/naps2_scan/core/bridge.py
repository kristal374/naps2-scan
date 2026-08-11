from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Self, cast

import pythonnet

NATIVE_BIN_DIR = Path(__file__).parent.resolve() / "native_bin"
NATIVE_BIN_PATH = NATIVE_BIN_DIR / "NAPS2Bridge.dll"
NATIVE_BIN_CONFIG = NATIVE_BIN_DIR / "NAPS2Bridge.runtimeconfig.json"

if not NATIVE_BIN_DIR.exists():
    raise RuntimeError(
        f"Native binary directory not found: {NATIVE_BIN_DIR}. "
        "The package was built without native binaries."
    )

pythonnet.load("coreclr", runtime_config=str(NATIVE_BIN_CONFIG))

import clr  # noqa: E402

clr.AddReference(str(NATIVE_BIN_PATH))

import System  # noqa

System.AppDomain.CurrentDomain.SetData(
    "APP_CONTEXT_BASE_DIRECTORY", str(NATIVE_BIN_DIR)
)
System.AppContext.SetData("APP_CONTEXT_BASE_DIRECTORY", str(NATIVE_BIN_DIR))

from NAPS2Bridge import Bridge  # noqa
from System.Threading import CancellationTokenSource  # noqa

BridgeType = type[Bridge]


class NAPS2Bridge:
    """
    Отвечает за прямую работу с жизненным циклом подключения к NAPS2.
    """

    _instance: NAPS2Bridge | None = None
    _instance_initialized: bool = False
    _instance_lock = threading.Lock()

    def __new__(cls) -> Self:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cast(Self, cls._instance)

    def __init__(self) -> None:
        if self._instance_initialized:
            return
        self._instance_initialized = True

        self._lock = threading.RLock()
        self._workers: set[uuid.UUID] = set()
        self._connection: BridgeType | None = None

    def _open(self) -> BridgeType:
        if self._connection is not None:
            return self._connection

        Bridge.Initialize()
        return Bridge

    def _close(self) -> None:
        if len(self._workers) != 0 or self._connection is None:
            return

        self._connection.Shutdown()
        self._connection = None

    def register_worker(self, worker_id: uuid.UUID) -> BridgeType:
        with self._lock:
            self._workers.add(worker_id)
            self._connection = self._open()
            return self._connection

    def unregister_worker(self, worker_id: uuid.UUID) -> None:
        with self._lock:
            self._workers.discard(worker_id)
            self._close()

    @staticmethod
    def make_cancel_token() -> CancellationTokenSource:
        return CancellationTokenSource()
