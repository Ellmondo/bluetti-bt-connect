"""The integration's actions.

read_registers: a read-only window onto any register, for exploring
addresses the device definition does not cover yet - see
Ellmondo/bluetti-bt-connect-lib#2 for leads. It cannot write: the library's
`DeviceReader.read_raw` only ever sends Modbus function 3.

set_schedule: replaces the EP2000's time-control schedule (up to six
charge/discharge/standby periods a day) in one write, the way BLUETTI's app
does it.
"""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import homeassistant.helpers.config_validation as cv

from bluetti_bt_connect_lib import FieldName, MAX_RAW_READ_COUNT
from bluetti_bt_connect_lib.enums import (
    CLOUD_CONTROLLED_EMS_MODES,
    EmsControlMode,
    WorkingMode,
)
from bluetti_bt_connect_lib.fields import ScheduleAction
from bluetti_bt_connect_lib.schedule import (
    SCHEDULE_SLOTS,
    ScheduleError,
    SchedulePeriod,
    validate_schedule,
)

from .const import DATA_COORDINATOR, DOMAIN, WRITE_SETTLE_SECONDS

_LOGGER = logging.getLogger(__name__)

SERVICE_READ_REGISTERS = "read_registers"
SERVICE_SET_SCHEDULE = "set_schedule"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_ADDRESS = "address"
ATTR_COUNT = "count"
ATTR_SLAVE = "slave"
ATTR_PERIODS = "periods"
ATTR_ACTION = "action"
ATTR_START = "start"
ATTR_END = "end"

SCHEDULE_ACTIONS = {
    "charge": ScheduleAction.CHARGE,
    "discharge": ScheduleAction.DISCHARGE,
    "standby": ScheduleAction.STANDBY,
}

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


PERIOD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ACTION): vol.All(
            cv.string, vol.Lower, vol.In(list(SCHEDULE_ACTIONS))
        ),
        vol.Required(ATTR_START): cv.time,
        vol.Required(ATTR_END): cv.time,
    }
)

SET_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_PERIODS): vol.All(
            cv.ensure_list, vol.Length(max=SCHEDULE_SLOTS), [PERIOD_SCHEMA]
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


async def _async_set_schedule(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    coordinator = _coordinator_for(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))

    if coordinator.reader is None or not hasattr(coordinator.reader, "write_schedule"):
        raise ServiceValidationError("This device has no time-control schedule")

    if coordinator.connection_released:
        raise ServiceValidationError(
            "The Bluetooth connection is released - turn the hold switch back on first"
        )

    data = coordinator.data or {}

    if FieldName.SCHEDULE_SLOT_1.value not in data:
        raise ServiceValidationError(
            "This device has not reported a time-control schedule"
        )

    # BLUETTI's AI mode and the cloud modes run the battery themselves and
    # overwrite manual settings, so the schedule would be undone.
    mode = data.get(FieldName.EMS_CONTROL_MODE.value)
    if mode in CLOUD_CONTROLLED_EMS_MODES:
        raise ServiceValidationError(
            f"The schedule is locked while the battery is under cloud control "
            f"({mode.name}). Change it in the BLUETTI app."
        )
    if mode == EmsControlMode.AI:
        raise ServiceValidationError(
            "BLUETTI AI mode overrides the schedule. Turn AI Control Mode off first."
        )

    periods = [
        SchedulePeriod(
            SCHEDULE_ACTIONS[period[ATTR_ACTION]],
            period[ATTR_START].replace(second=0, microsecond=0),
            period[ATTR_END].replace(second=0, microsecond=0),
        )
        for period in call.data[ATTR_PERIODS]
    ]

    try:
        periods = validate_schedule(periods)
    except ScheduleError as err:
        raise ServiceValidationError(str(err)) from err

    result = await coordinator.reader.write_schedule(periods)

    _LOGGER.info("set_schedule %s: %s", [str(p) for p in periods], result)

    if not result.accepted:
        raise HomeAssistantError(f"The schedule was not written - {result}")

    # Let the registers settle, then read the schedule back.
    await asyncio.sleep(WRITE_SETTLE_SECONDS)
    await coordinator.async_request_refresh()

    response = {
        "outcome": result.outcome.value,
        "periods": [str(p) for p in periods],
    }

    working_mode = (coordinator.data or {}).get(FieldName.WORKING_MODE.value)
    if working_mode is not None and working_mode != WorkingMode.CUSTOM:
        response["note"] = (
            f"Working mode is {working_mode.name}; the schedule only acts in CUSTOM."
        )

    return response


def async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's actions once."""

    if not hass.services.has_service(DOMAIN, SERVICE_READ_REGISTERS):

        async def handle_read(call: ServiceCall) -> ServiceResponse:
            return await _async_read_registers(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_READ_REGISTERS,
            handle_read,
            schema=READ_REGISTERS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_SCHEDULE):

        async def handle_schedule(call: ServiceCall) -> ServiceResponse:
            return await _async_set_schedule(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_SCHEDULE,
            handle_schedule,
            schema=SET_SCHEDULE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
