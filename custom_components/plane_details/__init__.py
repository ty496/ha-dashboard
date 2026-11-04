"""Plane details (2026-11-03): a second source for the planes over the house.

Flightradar24 honours the FAA's LADD list, so private aircraft whose owners asked come through as "Blocked", no
registration or callsign. adsb.lol is an unfiltered ADS-B network: this polls it for the area every 30 s, pairs its
aircraft with Flightradar24's flights (by registration, callsign, else nearest of the same type), and adds the
registered owner (adsbdb) and whether the aircraft is a notable one (plane-alert-db: celebrities' and billionaires'
jets, VIPs, governments). One sensor, sensor.plane_details, holds it for the dashboard: by_fr24 keyed by
Flightradar24's flight id, aircraft, notable. plane_details_notable fires when a person of interest's aircraft comes
into the area. Aircraft on the FAA's anonymous-address program (PIA) can't be named by anyone.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import PlaneDetailsCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = PlaneDetailsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
