from __future__ import annotations

import json
import queue
import threading
import uuid
from collections.abc import Callable, Iterator
from enum import Enum, auto
from types import TracebackType
from typing import Self

from PIL import Image

from ..enums import Driver
from ..types import ScanDevice, ScannerCapabilities, ScanOptions
from .bridge import BridgeType, NAPS2Bridge
from .decorator import dotnet_async
from .exception import wrap_scan_exception


class QueueSignal(Enum):
    DONE = auto()


class APIWorker:
    """
    Отвечает за прямую работу с API библиотеки NAPS2,
    разделяет этапы работы с подключением/инициализацией и данными,
    обеспечивая возможность одновременной работы нескольких процессов
    без опасений что другой процесс прервёт соединение.
    """

    def __init__(self) -> None:
        self.worker_id = uuid.uuid4()
        self._bridge = NAPS2Bridge()
        self._connection: BridgeType | None = None

        self._busy = threading.Lock()
        self._cancel_scan_token = None

    @property
    def connection(self) -> BridgeType:
        if self._connection is None:
            raise RuntimeError("No connection established.")
        return self._connection

    @dotnet_async
    def list_devices(
        self,
        driver: Driver = Driver.DEFAULT,
        *,
        timeout: float | None = None,
    ) -> list[ScanDevice]:
        with self._busy:
            timeout_ms = int(timeout * 1000) if timeout is not None else 0
            task = self.connection.GetDevicesAsync(driver.value, timeout_ms)
            device_list = json.loads(task.GetAwaiter().GetResult())
            return [ScanDevice(**device) for device in device_list]

    @dotnet_async
    def get_capabilities(self, device: ScanDevice) -> ScannerCapabilities:
        with self._busy:
            device_json = json.dumps(device.model_dump(mode="json", by_alias=True))
            task = self.connection.GetCapabilitiesAsync(device_json)
            capabilities = json.loads(task.GetAwaiter().GetResult())
            return ScannerCapabilities(**capabilities)

    def scan(
        self,
        device: ScanDevice,
        options: ScanOptions | None = None,
        *,
        on_scan_start: Callable[[], None] | None = None,
        on_scan_end: Callable[[], None] | None = None,
        on_page_start: Callable[[int], None] | None = None,
        on_page_progress: Callable[[int, float], None] | None = None,
        on_page_end: Callable[[int], None] | None = None,
    ) -> Iterator[Image.Image]:
        # Validate that the worker is connected before claiming the busy lock.
        # This raises RuntimeError immediately if open() was not called.
        _ = self.connection
        if not self._busy.acquire(blocking=False):
            raise RuntimeError("Worker is already busy with another operation")
        try:
            yield from self._scan_impl(
                device,
                options if options is not None else ScanOptions(),
                on_scan_start=on_scan_start,
                on_scan_end=on_scan_end,
                on_page_start=on_page_start,
                on_page_progress=on_page_progress,
                on_page_end=on_page_end,
            )
        finally:
            self._busy.release()

    def _scan_impl(
        self,
        device: ScanDevice,
        options: ScanOptions,
        *,
        on_scan_start: Callable[[], None] | None = None,
        on_scan_end: Callable[[], None] | None = None,
        on_page_start: Callable[[int], None] | None = None,
        on_page_progress: Callable[[int, float], None] | None = None,
        on_page_end: Callable[[int], None] | None = None,
    ) -> Iterator[Image.Image]:
        self._cancel_scan_token = self._bridge.make_cancel_token()
        image_queue: queue.Queue[Image.Image | QueueSignal | Exception] = queue.Queue(
            maxsize=1
        )

        def processed_new_image(
            raw_bytes: bytes, width: int, height: int, pixel_format: str
        ) -> None:
            image_queue.put(
                Image.frombytes(pixel_format, (width, height), bytes(raw_bytes))
            )

        def worker() -> None:
            from System import Action, Array, Byte, Double, Int32  # type: ignore[attr-defined] # fmt: skip # noqa

            options_json = json.dumps(
                {
                    **options.model_dump(mode="json", by_alias=True),
                    "device": device.model_dump(mode="json", by_alias=True),
                }
            )

            try:
                task = self.connection.ScanAsync(
                    options_json,
                    Action(on_scan_start) if on_scan_start else None,
                    Action(on_scan_end) if on_scan_end else None,
                    Action[int](on_page_start) if on_page_start else None,
                    Action[int](on_page_end) if on_page_end else None,
                    Action[Array[Byte], int, int, str](processed_new_image),
                    Action[Int32, Double](on_page_progress)
                    if on_page_progress
                    else None,
                    self._cancel_scan_token.Token,  # type: ignore[attr-defined]
                )
                task.Wait()
            except Exception as e:  # noqa: BLE001
                image_queue.put(e)
            else:
                image_queue.put(QueueSignal.DONE)

        scan_thread = threading.Thread(target=worker)
        scan_thread.start()

        try:
            while True:
                item = image_queue.get()
                if isinstance(item, QueueSignal):
                    break
                if isinstance(item, Exception):
                    raise wrap_scan_exception(item)
                yield item
        except BaseException:
            self.stop()
            raise
        finally:
            while scan_thread.is_alive():
                try:
                    image_queue.get(timeout=0.5)
                except queue.Empty:
                    pass
            scan_thread.join(timeout=5)
            self._cancel_scan_token = None

    def stop(self) -> None:
        if self._cancel_scan_token is not None:
            self._cancel_scan_token.Cancel()

    def create(self) -> Self:
        self._connection = self._bridge.register_worker(self.worker_id)
        return self

    def delete(self) -> None:
        self.stop()
        self._bridge.unregister_worker(self.worker_id)
        self._connection = None

    def __enter__(self) -> Self:
        return self.create()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.delete()
