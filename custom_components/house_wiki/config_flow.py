"""Config flow for the house wiki: a read-only GitHub token and the repo; options set which pages are in scope."""

from __future__ import annotations

from typing import Any

import aiohttp
import probatio

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import (
    CONF_BRANCH,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    CONF_MENTION_IN,
    CONF_MENTION_TERMS,
    CONF_REPO,
    DEFAULT_BRANCH,
    DEFAULT_EXCLUDE,
    DEFAULT_INCLUDE,
    DEFAULT_MENTION_IN,
    DEFAULT_MENTION_TERMS,
    DOMAIN,
)
from .coordinator import API, TIMEOUT, github_headers

MULTILINE = TextSelector(TextSelectorConfig(multiline=True))


class HouseWikiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the token and repo, and check that the token can read the repo."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            repo = user_input[CONF_REPO].strip().strip("/")
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    f"{API}/repos/{repo}", headers=github_headers(user_input[CONF_TOKEN].strip()), timeout=TIMEOUT
                ) as resp:
                    status = resp.status
            except (aiohttp.ClientError, TimeoutError):
                status = 0
            if status == 200:
                return self.async_create_entry(
                    title="House wiki",
                    data={
                        CONF_TOKEN: user_input[CONF_TOKEN].strip(),
                        CONF_REPO: repo,
                        CONF_BRANCH: user_input.get(CONF_BRANCH, DEFAULT_BRANCH).strip() or DEFAULT_BRANCH,
                    },
                )
            errors["base"] = "cannot_connect" if status == 0 else "invalid_auth"
        schema = probatio.Schema(
            {
                probatio.Required(CONF_TOKEN): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                probatio.Required(CONF_REPO): str,
                probatio.Optional(CONF_BRANCH, default=DEFAULT_BRANCH): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HouseWikiOptionsFlow()


class HouseWikiOptionsFlow(OptionsFlow):
    """Which pages are in scope. One entry per line."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        opts = self.config_entry.options
        schema = probatio.Schema(
            {
                probatio.Optional(CONF_INCLUDE, default=opts.get(CONF_INCLUDE, DEFAULT_INCLUDE)): MULTILINE,
                probatio.Optional(CONF_MENTION_IN, default=opts.get(CONF_MENTION_IN, DEFAULT_MENTION_IN)): MULTILINE,
                probatio.Optional(
                    CONF_MENTION_TERMS, default=opts.get(CONF_MENTION_TERMS, DEFAULT_MENTION_TERMS)
                ): MULTILINE,
                probatio.Optional(CONF_EXCLUDE, default=opts.get(CONF_EXCLUDE, DEFAULT_EXCLUDE)): MULTILINE,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
