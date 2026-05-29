from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict


class TaskQueue:
    """A minimal in-process async task queue for background work.

    This is intentionally lightweight: it gives us a place to register and
    enqueue background jobs during Phase 2 without pulling in an external
    dependency (Celery/RQ). For production, wire a proper task queue.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._max_workers = max_workers
        self._registry: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def register(self, name: str):
        def _decorator(fn: Callable[..., Awaitable[Any]]):
            self._registry[name] = fn
            return fn

        return _decorator

    async def _worker(self) -> None:
        while self._running:
            try:
                name, args, kwargs = await self._queue.get()
            except asyncio.CancelledError:
                break
            try:
                fn = self._registry.get(name)
                if fn is None:
                    # Unknown task; skip
                    continue
                await fn(*args, **kwargs)
            except Exception:
                # Swallow exceptions here; real systems should log/handle them
                pass
            finally:
                self._queue.task_done()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for _ in range(self._max_workers):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(self, name: str, *args: Any, **kwargs: Any) -> None:
        await self._queue.put((name, args, kwargs))


# Singleton queue instance for convenience
default_queue = TaskQueue()
