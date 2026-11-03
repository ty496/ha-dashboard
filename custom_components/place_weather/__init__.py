"""Weather anywhere: a voice-agent tool for current weather and the forecast at any place (2026-11-03).

Web pages fill in live weather with scripts, so a web search or fetch sees stale numbers. This asks Open-Meteo
directly (free, no key): the place name goes to its geocoder (weather.py picks the right match), then the forecast
comes back in °F, mph and inches. Offered to conversation agents as the LLM API "Weather anywhere".
"""

from __future__ import annotations

from typing import Any, override

import aiohttp
import probatio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .config_flow import DOMAIN
from .weather import choose, label, shape, split_place

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = aiohttp.ClientTimeout(total=15)
API_PROMPT = (
    "For weather anywhere other than home (another town, a mountain, a ski area, a trip destination), use "
    "get_place_weather instead of searching the web; web pages show stale weather. For spots that aren't towns, "
    "such as ski areas, passes or trailheads, pass their latitude and longitude."
)


class PlaceWeatherTool(llm.Tool):
    """Current conditions, the next hours and the coming days for one place."""

    name = "get_place_weather"
    description = (
        "Live weather for any place: current conditions, the next 12 hours and a daily forecast. Give a place "
        "name ('Vail', 'Paris, France', 'Moab, Utah') or, for spots that aren't towns, latitude and longitude."
    )
    parameters = probatio.Schema(
        {
            probatio.Optional("place", description="Town or city, optionally with state or country."): str,
            probatio.Optional("latitude", description="Exact spot instead of a town."): float,
            probatio.Optional("longitude", description="Exact spot instead of a town."): float,
            probatio.Optional("days", description="Days of daily forecast, 1 to 7 (default 3)."): int,
        }
    )
    annotations = llm.ToolAnnotations(read_only=True, destructive=False, idempotent=True, open_world=True)
    integration = DOMAIN

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> llm.ToolResult:
        args: dict[str, Any] = tool_input.tool_args
        place = (args.get("place") or "").strip()
        lat, lon = args.get("latitude"), args.get("longitude")
        days = max(1, min(int(args.get("days") or 3), 7))
        session = async_get_clientsession(hass)
        try:
            if lat is None or lon is None:
                if not place:
                    return llm.ToolResult(data={"error": "Give a place name or a latitude and longitude."}, error=True)
                name, quals = split_place(place)
                async with session.get(
                    GEOCODE, params={"name": name, "count": "10", "language": "en", "format": "json"}, timeout=TIMEOUT
                ) as resp:
                    resp.raise_for_status()
                    found = (await resp.json()).get("results") or []
                hit = choose(found, quals, (hass.config.latitude, hass.config.longitude))
                if hit is None:
                    return llm.ToolResult(
                        data={"error": f"Couldn't find '{place}'. Try adding the state or country, or give coordinates."},
                        error=True,
                    )
                lat, lon, where = hit["latitude"], hit["longitude"], label(hit)
            else:
                where = place or f"{lat:.3f}, {lon:.3f}"
            params = {
                "latitude": str(lat),
                "longitude": str(lon),
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,snowfall,"
                "weather_code,wind_speed_10m,wind_gusts_10m",
                "hourly": "temperature_2m,precipitation_probability,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                "precipitation_sum,snowfall_sum,wind_speed_10m_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "auto",
                "forecast_days": str(max(days, 2)),
            }
            async with session.get(FORECAST, params=params, timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                forecast = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            return llm.ToolResult(data={"error": f"Open-Meteo didn't answer: {err}"}, error=True)
        result = shape(where, forecast)
        result["days"] = result["days"][:days]
        return llm.ToolResult(data=result)


class PlaceWeatherAPI(llm.API):
    """The tool, offered as one API that a conversation agent can be given."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass=hass, id=DOMAIN, name="Weather anywhere")

    @override
    async def async_get_api_instance(self, llm_context: llm.LLMContext) -> llm.APIInstance:
        return llm.APIInstance(self, API_PROMPT, llm_context, tools=[PlaceWeatherTool()])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry.async_on_unload(llm.async_register_api(hass, PlaceWeatherAPI(hass)))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
