"""Config flow for Weather anywhere: one confirm step (Open-Meteo needs no account or key)."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

DOMAIN = "place_weather"


class PlaceWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the weather tool for voice agents."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user")
        return self.async_create_entry(title="Weather anywhere", data={})
