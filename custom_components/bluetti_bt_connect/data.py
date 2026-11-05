"""What a loaded config entry keeps at runtime (entry.runtime_data)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from bluetti_bt_connect_lib import DeviceConnection

from .coordinator import PollingCoordinator


@dataclass
class BluettiData:
    """The shared pieces every platform and action of one battery uses."""

    coordinator: PollingCoordinator
    lock: asyncio.Lock
    """Serialises polls and writes, so they never overlap on the device."""
    connection: DeviceConnection
    """The one Bluetooth connection, shared by polling and every control."""


type BluettiConfigEntry = ConfigEntry[BluettiData]
