"""Bluetti Bluetooth Integration"""

from __future__ import annotations
import asyncio
import re
import logging
from typing import List
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .utils import mac_loggable
from bluetti_bt_connect_lib import DeviceConnection

from .const import DOMAIN, MANUFACTURER
from .data import BluettiConfigEntry, BluettiData
from .services import async_register_services
from .shutdown import release_connection
from .types import FullDeviceConfig
from .coordinator import PollingCoordinator

PLATFORMS: List[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
]


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration-wide actions."""
    async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BluettiConfigEntry) -> bool:
    """Set up Bluetti Powerstation from a config entry."""

    config = FullDeviceConfig.from_dict(entry.data)

    if config is None:
        # Not something a retry fixes: the entry has to be set up again.
        raise ConfigEntryError(
            f"Could not read the settings of '{entry.title}'. Remove the "
            "device and add it again. (This can happen after upgrading from "
            "v0.1.6, whose entries lack the 'use_encryption' field.)"
        )

    logger = logging.getLogger(
        f"{__name__}.{mac_loggable(config.address).replace(':', '_')}"
    )

    logger.debug("Init Bluetti BT Integration")

    if not bluetooth.async_address_present(hass, config.address):
        raise ConfigEntryNotReady("Bluetti device not present")

    # One lock, so polls and writes never overlap on the device.
    lock = asyncio.Lock()

    # One connection, shared by polling and every control. Previously each
    # write opened its own link, which could tear down the connection a poll
    # was using and cost two connect cycles per button press.
    #
    # The device lookup is handed to the library as a callable so it can use
    # Home Assistant's own cache, which answers instantly and picks the best
    # proxy path, instead of running a five-second scan of its own.
    def ble_device():
        return bluetooth.async_ble_device_from_address(
            hass, config.address, connectable=True
        )

    connection = DeviceConnection(config.address, device_provider=ble_device)

    # Create coordinator for polling
    logger.debug("Creating coordinator")
    coordinator = PollingCoordinator(
        hass,
        entry,
        config,
        lock,
        connection,
    )

    # Close the link properly when Home Assistant stops, instead of leaving
    # it to be cut when the process exits. Registered before the first
    # refresh so a stop during the initial connection is covered too.
    async def _release_on_stop(_event: Event) -> None:
        coordinator.closing = True
        await release_connection(lock, connection, logger)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _release_on_stop)
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = BluettiData(coordinator, lock, connection)

    logger.debug("Creating entities")
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    logger.debug("Setup done")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BluettiConfigEntry) -> bool:
    """Tear down the entry, releasing the BLE connection.

    Without this the shared connection outlives a reload: the link stays up,
    keeps consuming one of the proxy's connection slots, and keeps the
    Bluetti phone app locked out, while a second connection is built
    alongside it on the next setup.
    """

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unloaded:
        return False

    data: BluettiData = entry.runtime_data
    data.coordinator.closing = True

    # Same clean close as at shutdown - never mid-conversation.
    await release_connection(data.lock, data.connection, data.coordinator.logger)

    return True


def device_info(entry: ConfigEntry):
    """Device info."""
    config = FullDeviceConfig.from_dict(entry.data)

    if config is None:
        return None

    return DeviceInfo(
        identifiers={(DOMAIN, config.address)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        model=config.dev_type,
    )


def get_unique_id(name: str, sensor_type: str | None = None):
    """Generate an unique id."""
    res = re.sub("[^A-Za-z0-9]+", "_", name).lower()
    if sensor_type is not None:
        return f"{sensor_type}.{res}"
    return res
