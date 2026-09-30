"""Tests for the clean Bluetooth disconnect used at shutdown and unload."""

import asyncio
import importlib
import logging
import pathlib
import sys
import types
import unittest

# Import shutdown.py without running the integration's __init__.py, which
# needs Home Assistant. A stand-in package pointing at the same directory
# lets the module's relative import of .const resolve normally.
_COMPONENT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components"
    / "bluetti_bt_connect"
)
_package = types.ModuleType("_bluetti_component")
_package.__path__ = [str(_COMPONENT)]
sys.modules.setdefault("_bluetti_component", _package)

release_connection = importlib.import_module(
    "_bluetti_component.shutdown"
).release_connection


class FakeConnection:
    def __init__(self, events, fail=False):
        self.events = events
        self.fail = fail
        self.disconnects = 0

    async def disconnect(self):
        self.disconnects += 1
        self.events.append("disconnect")
        if self.fail:
            raise RuntimeError("disconnect failed")


async def poll(lock, events, duration):
    async with lock:
        events.append("poll start")
        await asyncio.sleep(duration)
        events.append("poll end")


class TestReleaseConnection(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.events = []
        self.lock = asyncio.Lock()
        self.connection = FakeConnection(self.events)
        self.logger = logging.getLogger("test")

    async def test_idle_disconnects_immediately(self):
        await release_connection(self.lock, self.connection, self.logger, wait=1)

        self.assertEqual(self.events, ["disconnect"])
        self.assertFalse(self.lock.locked())

    async def test_waits_for_poll_in_progress(self):
        task = asyncio.create_task(poll(self.lock, self.events, 0.2))
        await asyncio.sleep(0)

        await release_connection(self.lock, self.connection, self.logger, wait=2)
        await task

        self.assertEqual(self.events, ["poll start", "poll end", "disconnect"])
        self.assertFalse(self.lock.locked())

    async def test_stuck_conversation_does_not_stall_shutdown(self):
        task = asyncio.create_task(poll(self.lock, self.events, 5))
        await asyncio.sleep(0)

        loop = asyncio.get_running_loop()
        started = loop.time()
        with self.assertLogs("test", level="WARNING"):
            await release_connection(
                self.lock, self.connection, self.logger, wait=0.2
            )
        elapsed = loop.time() - started

        self.assertLess(elapsed, 1)
        self.assertEqual(self.connection.disconnects, 1)
        # The lock still belongs to the stuck conversation - never released
        # on its behalf.
        self.assertTrue(self.lock.locked())
        task.cancel()

    async def test_lock_released_even_if_disconnect_raises(self):
        connection = FakeConnection(self.events, fail=True)

        with self.assertRaises(RuntimeError):
            await release_connection(self.lock, connection, self.logger, wait=1)

        self.assertFalse(self.lock.locked())


if __name__ == "__main__":
    unittest.main()
