"""Fixed-size pool of reusable Playwright Chromium browsers.

Playwright's sync API is not thread-safe across OS threads: a Browser can only
be driven from the exact thread that started its `sync_playwright()` instance
(calling from another thread raises a greenlet error). FastAPI runs sync route
handlers on a threadpool, so instead of lending out raw Browser objects, each
pool slot is a dedicated worker thread that owns its own Playwright instance +
browser for its entire lifetime and executes submitted jobs on itself.
"""
import os
import queue
import threading
import logging
from concurrent.futures import Future
from typing import Callable, List, Optional, TypeVar

from playwright.sync_api import sync_playwright, Browser

logger = logging.getLogger(__name__)

DEFAULT_POOL_SIZE = 3

T = TypeVar("T")


class _BrowserWorker:
    """Owns one Playwright instance + one Chromium browser for its whole life,
    both created and used exclusively on this worker's own thread."""

    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self._jobs: "queue.Queue" = queue.Queue()
        self._ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name=f"playwright-worker-{worker_id}", daemon=True
        )

    def start(self) -> None:
        self._thread.start()
        self._ready.wait()

    def _run(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            logger.info("Playwright worker %d launched", self.worker_id)
            self._ready.set()
            while True:
                job = self._jobs.get()
                if job is None:
                    break
                func, future = job
                try:
                    result = func(browser)
                except BaseException as e:  # noqa: BLE001 - propagate to caller thread
                    future.set_exception(e)
                else:
                    future.set_result(result)
            browser.close()
            logger.info("Playwright worker %d closed", self.worker_id)

    def submit(self, func: Callable[[Browser], T]) -> T:
        future: "Future[T]" = Future()
        self._jobs.put((func, future))
        return future.result()

    def stop(self) -> None:
        self._jobs.put(None)
        self._thread.join(timeout=10)


class BrowserPool:
    def __init__(self, size: Optional[int] = None):
        self.size = size or int(os.getenv("PLAYWRIGHT_POOL_SIZE", DEFAULT_POOL_SIZE))
        self._workers: List[_BrowserWorker] = []
        self._available: "queue.Queue[_BrowserWorker]" = queue.Queue()

    def start(self) -> None:
        for i in range(self.size):
            worker = _BrowserWorker(i)
            worker.start()
            self._workers.append(worker)
            self._available.put(worker)
        logger.info("Browser pool started with %d worker(s)", self.size)

    def stop(self) -> None:
        for worker in self._workers:
            worker.stop()
        self._workers.clear()
        logger.info("Browser pool stopped")

    def run(self, func: Callable[[Browser], T]) -> T:
        """Borrow a worker (blocking if all are busy), run func(browser) on the
        worker's own thread, and always return the worker to the pool."""
        worker = self._available.get(block=True)
        try:
            return worker.submit(func)
        finally:
            self._available.put(worker)


browser_pool = BrowserPool()
