"""Graceful startup/shutdown with proper task cancellation on timeout."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

ShutdownHook = Callable[[], Awaitable[None]]
StartupHook = Callable[[], Awaitable[None]]

_startup_hooks: list[StartupHook] = []
_shutdown_hooks: list[ShutdownHook] = []
_shutdown_event = asyncio.Event()


def register_startup(hook: StartupHook) -> StartupHook:
    _startup_hooks.append(hook)
    return hook


def register_shutdown(hook: ShutdownHook) -> ShutdownHook:
    _shutdown_hooks.append(hook)
    return hook


def shutdown_requested() -> bool:
    return _shutdown_event.is_set()


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def _on_signal(sig: signal.Signals) -> None:
        logger.info("Received %s — beginning graceful shutdown", sig.name)
        _shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _on_signal, sig)
        except NotImplementedError:
            logger.debug("Signal handler for %s not supported on this platform", sig)


async def _run_hook_with_timeout(hook: ShutdownHook, timeout: float = 15.0) -> None:
    """Run a shutdown hook and cancel the underlying task if it times out."""
    name = getattr(hook, "__name__", repr(hook))
    task = asyncio.ensure_future(hook())
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
    except TimeoutError:
        logger.warning("Shutdown hook %s exceeded %.0fs — cancelling", name, timeout)
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    except Exception:
        logger.exception("Shutdown hook %s raised an error", name)
        if not task.done():
            task.cancel()


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    """FastAPI lifespan: runs registered hooks; cancels stuck hooks on timeout."""
    loop = asyncio.get_event_loop()
    _install_signal_handlers(loop)

    for hook in _startup_hooks:
        try:
            await hook()
        except Exception:
            logger.exception("Startup hook %s failed", getattr(hook, "__name__", hook))
            raise

    try:
        yield
    finally:
        for hook in reversed(_shutdown_hooks):
            await _run_hook_with_timeout(hook)
        _shutdown_event.set()
