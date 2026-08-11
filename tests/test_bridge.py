from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from naps2_scan.core import bridge as bridge_module
from naps2_scan.core.bridge import NAPS2Bridge


class FakeBridge:
    def __init__(self):
        self.Initialize = MagicMock()
        self.Shutdown = MagicMock()


@pytest.fixture(autouse=True)
def reset_singleton():
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False
    yield
    NAPS2Bridge._instance = None
    NAPS2Bridge._instance_initialized = False


@pytest.fixture
def patched_bridge(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(bridge_module, "Bridge", fake)
    return fake


def test_singleton_returns_same_instance() -> None:
    a = NAPS2Bridge()
    b = NAPS2Bridge()

    assert a is b


def test_init_is_idempotent(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    bridge._workers.add(uuid.uuid4())

    same = NAPS2Bridge()

    assert same is bridge
    assert same._workers is bridge._workers
    assert len(bridge._workers) == 1


def test_register_worker_opens_connection(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    worker_id = uuid.uuid4()

    connection = bridge.register_worker(worker_id)

    assert worker_id in bridge._workers
    assert connection is patched_bridge
    assert bridge._connection is patched_bridge
    patched_bridge.Initialize.assert_called_once()


def test_register_same_worker_is_idempotent(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    worker_id = uuid.uuid4()

    bridge.register_worker(worker_id)
    bridge.register_worker(worker_id)

    assert len(bridge._workers) == 1
    patched_bridge.Initialize.assert_called_once()


def test_unregister_worker_removes_worker(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    worker_id = uuid.uuid4()
    bridge.register_worker(worker_id)

    bridge.unregister_worker(worker_id)

    assert worker_id not in bridge._workers


def test_close_keeps_connection_if_workers_remain(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    worker_a = uuid.uuid4()
    worker_b = uuid.uuid4()
    bridge.register_worker(worker_a)
    bridge.register_worker(worker_b)

    bridge.unregister_worker(worker_a)

    assert worker_b in bridge._workers
    assert bridge._connection is patched_bridge
    patched_bridge.Shutdown.assert_not_called()


def test_close_shuts_down_when_last_worker_removed(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    worker_id = uuid.uuid4()
    bridge.register_worker(worker_id)

    bridge.unregister_worker(worker_id)

    patched_bridge.Shutdown.assert_called_once()
    assert bridge._connection is None


def test_open_returns_existing_connection(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    bridge.register_worker(uuid.uuid4())
    patched_bridge.Initialize.reset_mock()

    connection = bridge._open()

    patched_bridge.Initialize.assert_not_called()
    assert connection is patched_bridge


def test_close_does_nothing_when_not_opened(patched_bridge) -> None:
    bridge = NAPS2Bridge()

    bridge._close()

    patched_bridge.Shutdown.assert_not_called()


def test_make_cancel_token(patched_bridge) -> None:
    token_source = NAPS2Bridge.make_cancel_token()

    assert token_source is not None
    assert not token_source.Token.IsCancellationRequested
    token_source.Cancel()
    assert token_source.Token.IsCancellationRequested


def test_initialize_failure_leaves_connection_closed(patched_bridge) -> None:
    bridge = NAPS2Bridge()
    patched_bridge.Initialize.side_effect = RuntimeError("init failed")

    with pytest.raises(RuntimeError, match="init failed"):
        bridge.register_worker(uuid.uuid4())

    assert bridge._connection is None
