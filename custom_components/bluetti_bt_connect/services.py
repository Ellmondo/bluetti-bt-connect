"""The read_registers action: a read-only window onto any register.

For exploring addresses the device definition does not cover yet - see
Ellmondo/bluetti-bt-connect-lib#2 for leads. Nothing here can write: the
library's `DeviceReader.read_raw` only ever sends Modbus function 3.
"""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from bluetti_bt_connect_lib import MAX_RAW_READ_COUNT

from .const import DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_READ_REGISTERS = "read_registers"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_ADDRESS = "address"
ATTR_COUNT = "count"
ATTR_SLAVE = "slave"

POLL_SLAVE = 1
"""The slave normal polling reads from - always allowed."""

READ_REGISTERS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_ADDRESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=0xFFFF)
        ),
        vol.Optional(ATTR_COUNT, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=MAX_RAW_READ_COUNT)
        ),
        vol.Optional(ATTR_SLAVE, default=POLL_SLAVE): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=247)
        ),
    }
)


def _coordinator_for(hass: HomeAssistant, entry_id: str | None):
    """The coordinator of the battery the call is aimed at."""

    loaded = {
        key: value
        for key, value in hass.data.get(DOMAIN, {}).items()
        if isinstance(value, dict) and DATA_COORDINATOR in value
    }

    if entry_id is not None:
        if entry_id not in loaded:
            raise ServiceValidationError(
                f"No loaded Bluetti BT Connect entry with id {entry_id}"
            )
        return loaded[entry_id][DATA_COORDINATOR]

    if len(loaded) == 1:
        return next(iter(loaded.values()))[DATA_COORDINATOR]

    if not loaded:
        raise ServiceValidationError("No Bluetti BT Connect device is loaded")

    raise ServiceValidationError(
        "More than one Bluetti device is set up - choose one with config_entry_id"
    )


async def _async_read_registers(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    coordinator = _coordinator_for(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
    address = call.data[ATTR_ADDRESS]
    count = call.data[ATTR_COUNT]
    slave = call.data[ATTR_SLAVE]

    if coordinator.reader is None:
        raise ServiceValidationError("This device type has no reader")

    if coordinator.connection_released:
        # The connection is handed over (or Home Assistant is stopping).
        # Reading would take it straight back, which is what releasing it
        # was meant to prevent.
        raise ServiceValidationError(
            "The Bluetooth connection is released - turn the hold switch back on first"
        )

    if address + count > 0x10000:
        raise ServiceValidationError(
            f"address {address} + count {count} runs past register 65535"
        )

    if slave != POLL_SLAVE:
        # Only ever address a device the battery itself says is there.
        # Asking a slave address nothing answers on is at best a timeout,
        # and on some BLUETTI firmware a request to an unexpected unit id
        # has hung the Modbus stack until a power cycle.
        nodes = await coordinator.reader.read_nodes()

        if nodes is None:
            raise ServiceValidationError(
                "Could not read the battery's node list to check that slave "
                f"{slave} exists - try again"
            )

        known = sorted({node.slave for node in nodes} | {POLL_SLAVE})

        if slave not in known:
            raise ServiceValidationError(
                f"Slave {slave} is not in the battery's node list. "
                f"Devices on this system: {', '.join(str(s) for s in known)}"
            )

    result = await coordinator.reader.read_raw(address, count, slave)

    _LOGGER.info(
        "read_registers %d+%d at slave %d: %s",
        address,
        count,
        slave,
        result.outcome.value,
    )

    return result.as_dict()


def async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's actions once."""

    if hass.services.has_service(DOMAIN, SERVICE_READ_REGISTERS):
        return

    async def handle(call: ServiceCall) -> ServiceResponse:
        return await _async_read_registers(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_REGISTERS,
        handle,
        schema=READ_REGISTERS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
