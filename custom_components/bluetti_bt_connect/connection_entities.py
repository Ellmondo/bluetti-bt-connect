"""Diagnostic entities describing the Bluetooth connection itself.

They answer "is it connected, and if not, since when and why" without
reading the log. In particular they show the BLUETTI Bluetooth lock-up as it
happens: the connection drops, failures start counting up and the last
successful poll stops moving, while the device carries on over WiFi.

Unlike the device's own entities these are not driven only by the
coordinator. Home Assistant stops notifying coordinator listeners after the
second failed refresh in a row, which is exactly when these matter, so they
also poll themselves every 30 seconds (the platform default) and simply
report the connection's current state. Nothing they do touches the device.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo

from . import get_unique_id
from .coordinator import PollingCoordinator


@dataclass(frozen=True)
class ConnectionSensorDescription:
    key: str
    value: Callable[[PollingCoordinator], Any]
    icon: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


CONNECTION_SENSORS = (
    ConnectionSensorDescription(
        key="connection_failures",
        value=lambda c: c.connection.consecutive_failures,
        icon="mdi:bluetooth-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ConnectionSensorDescription(
        key="last_successful_poll",
        value=lambda c: c.last_success_time,
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    ConnectionSensorDescription(
        key="connected_since",
        value=lambda c: c.connection.connected_since,
        icon="mdi:bluetooth-connect",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    ConnectionSensorDescription(
        key="requests_on_connection",
        value=lambda c: c.connection.requests_served,
        icon="mdi:swap-horizontal",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ConnectionSensorDescription(
        key="bluetooth_connections",
        value=lambda c: c.connection.connect_count,
        icon="mdi:bluetooth-transfer",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)


class _ConnectionEntity:
    """Shared plumbing: diagnostic, always available, polled and pushed."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = True

    def _setup(
        self, coordinator: PollingCoordinator, device_info: DeviceInfo, key: str
    ) -> None:
        self.coordinator = coordinator
        self._attr_device_info = device_info
        self._attr_translation_key = key
        self._attr_unique_id = get_unique_id(f"{device_info.get('name')} {key}")

    @property
    def available(self) -> bool:
        return self.coordinator.connection is not None

    async def async_added_to_hass(self) -> None:
        # Also refresh straight after every poll, not only every 30 seconds.
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class BluettiConnectionSensor(_ConnectionEntity, SensorEntity):
    def __init__(
        self,
        coordinator: PollingCoordinator,
        device_info: DeviceInfo,
        description: ConnectionSensorDescription,
    ) -> None:
        self._setup(coordinator, device_info, description.key)
        self._description = description
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def native_value(self) -> Any:
        if not self.available:
            return None
        return self._description.value(self.coordinator)


class BluettiConnectedBinarySensor(_ConnectionEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, coordinator: PollingCoordinator, device_info: DeviceInfo
    ) -> None:
        self._setup(coordinator, device_info, "bluetooth_connected")

    @property
    def is_on(self) -> bool:
        connection = self.coordinator.connection
        return connection is not None and connection.is_connected


def connection_sensors(
    coordinator: PollingCoordinator, device_info: DeviceInfo
) -> list[BluettiConnectionSensor]:
    if coordinator.connection is None:
        return []
    return [
        BluettiConnectionSensor(coordinator, device_info, description)
        for description in CONNECTION_SENSORS
    ]


def connection_binary_sensors(
    coordinator: PollingCoordinator, device_info: DeviceInfo
) -> list[BluettiConnectedBinarySensor]:
    if coordinator.connection is None:
        return []
    return [BluettiConnectedBinarySensor(coordinator, device_info)]
