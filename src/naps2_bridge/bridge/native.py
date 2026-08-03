from __future__ import annotations

from pathlib import Path
from typing import Any

import clr  # pythonnet


_BRIDGE_ASSEMBLY = "NAPS2Bridge"
_NATIVE_BIN_DIR = Path(__file__).parent / "native_bin"


def load_bridge_assembly() -> Any:
    raise NotImplementedError
