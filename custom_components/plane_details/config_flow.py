"""Config flow for Plane details: one confirm step (adsb.lol, adsbdb and plane-alert-db need no account)."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

DOMAIN = "plane_details"


class PlaneDetailsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the second plane source."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user")
        return self.async_create_entry(title="Plane details", data={})
