"""Config flow for CalDAV edit: one confirm step, no settings (it reuses the CalDAV integration's login)."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class CaldavEditConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the update/delete event actions."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm and create the entry."""
        if user_input is None:
            return self.async_show_form(step_id="user")
        return self.async_create_entry(title="CalDAV edit", data={})
