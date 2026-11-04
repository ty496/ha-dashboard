"""sensor.plane_details: how many aircraft adsb.lol sees round home, and what is known about them."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PlaneDetailsCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([PlaneDetailsSensor(entry.runtime_data, entry)])


class PlaneDetailsSensor(CoordinatorEntity[PlaneDetailsCoordinator], SensorEntity):
    """The aircraft overhead (adsb.lol), with owners and notable aircraft, and Flightradar24's flights paired."""

    _attr_name = "Plane details"
    _attr_icon = "mdi:airplane-search"
    _attr_native_unit_of_measurement = "aircraft"
    _attr_state_class = SensorStateClass.MEASUREMENT
    # A few kilobytes every 30 s: kept out of the recorder.
    _unrecorded_attributes = frozenset({"aircraft", "by_fr24", "notable"})

    def __init__(self, coordinator: PlaneDetailsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_aircraft"
        self.entity_id = "sensor.plane_details"

    @property
    def native_value(self) -> int:
        return len((self.coordinator.data or {}).get("aircraft") or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {k: data.get(k) for k in ("by_fr24", "notable", "aircraft")}
