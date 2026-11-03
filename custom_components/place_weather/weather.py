"""The weather entity behind the place pop-up: the last place the voice agent looked up (2026-11-03).

get_place_weather hands each answer to this entity, which takes the place's name and its forecast, so a
dashboard's weather-forecast card (the Show's #place-weather pop-up) can draw it like the home forecast.
It holds nothing until the first lookup and nothing across restarts.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import Forecast, WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .config_flow import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    entity = PlaceWeatherEntity()
    hass.data.setdefault(DOMAIN, {})["entity"] = entity
    async_add_entities([entity])


class PlaceWeatherEntity(WeatherEntity):
    """Current conditions and forecasts for the last place asked about, named after it."""

    _attr_should_poll = False
    _attr_unique_id = "place_weather_last"
    _attr_name = "Place weather"
    _attr_attribution = "Weather from Open-Meteo"
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_native_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.INCHES
    _attr_native_pressure_unit = UnitOfPressure.HPA

    def __init__(self) -> None:
        self._hourly: list[Forecast] = []
        self._daily: list[Forecast] = []

    async def async_show(
        self, place: str, now: dict[str, Any], hourly: list[dict[str, Any]], daily: list[dict[str, Any]]
    ) -> None:
        """Take on a new place: its name, its weather now and both forecasts, pushed to open cards."""
        self._attr_name = place
        self._attr_condition = now["condition"]
        self._attr_native_temperature = now["temperature"]
        self._attr_native_apparent_temperature = now["apparent"]
        self._attr_humidity = now["humidity"]
        self._attr_native_wind_speed = now["wind"]
        self._attr_native_wind_gust_speed = now["gusts"]
        self._attr_wind_bearing = now["bearing"]
        self._attr_native_pressure = now["pressure"]
        self._hourly = [Forecast(**h) for h in hourly]
        self._daily = [Forecast(**d) for d in daily]
        self.async_write_ha_state()
        await self.async_update_listeners(("daily", "hourly"))

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return self._daily or None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        return self._hourly or None
