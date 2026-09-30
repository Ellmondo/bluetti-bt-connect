"""Letting go of the Bluetooth link cleanly.

The device accepts one central at a time and the connection is held open
permanently. If Home Assistant simply exits, the link is cut wherever it
happens to be - possibly part-way through a poll or a write - and only torn
down afterwards, when the proxy notices Home Assistant has gone. A cut like
that can leave the EP2000 believing the old central is still attached, and
it then refuses every new connection until the battery is restarted.

This module has no Home Assistant imports so it can be tested on its own.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from .const import RELEASE_WAIT_SECONDS

if TYPE_CHECKING:
    from bluetti_bt_connect_lib import DeviceConnection


async def release_connection(
    lock: asyncio.Lock,
    connection: DeviceConnection,
    logger: logging.Logger,
    wait: float = RELEASE_WAIT_SECONDS,
) -> None:
    """Wait for the conversation in progress to finish, then disconnect.

    Polls and writes both hold ``lock`` for the whole of a conversation with
    the device, so acquiring it guarantees the disconnect lands between
    conversations rather than in the middle of one.

    The wait is bounded. A connection attempt that is still retrying can
    hold the lock for much longer than a poll takes, and shutdown cannot
    stall on it - after ``wait`` seconds the link is closed regardless.
    """

    try:
        async with asyncio.timeout(wait):
            await lock.acquire()
    except TimeoutError:
        logger.warning(
            "Device still busy after %ss - closing the Bluetooth connection anyway",
            wait,
        )
        await connection.disconnect()
        return

    try:
        logger.info("Closing the Bluetooth connection")
        await connection.disconnect()
    finally:
        lock.release()
