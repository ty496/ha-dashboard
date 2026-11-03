"""House wiki: read-only access to the household's notes for Home Assistant's voice agents (2026-11-03).

Pages come from a private GitHub repo (an Obsidian vault) through a read-only token, limited to the paths and
pages the entry's options put in scope (coordinator.py). They are offered to conversation agents as an LLM API,
"House wiki", with two read-only tools: search the pages, and read one page (or just its matching sections).
"""

from __future__ import annotations

from typing import Any, override

import probatio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm

from .const import DOMAIN
from .coordinator import WikiCoordinator
from .wiki import read, search

API_PROMPT = (
    "The house wiki holds this household's notes about the home: its smart-home devices, automations and network, "
    "repairs and contractors, utilities, the radon system and the inspection report. Search it before answering "
    "questions about the house's history, settings, devices or service providers, then answer briefly in your own "
    "words. Never read long passages aloud. The wiki is read-only."
)
READ_ONLY = llm.ToolAnnotations(read_only=True, destructive=False, idempotent=True, open_world=False)


class SearchTool(llm.Tool):
    """Find pages by keywords."""

    name = "search_house_wiki"
    description = "Search the house wiki. Returns the best-matching pages with short excerpts."
    parameters = probatio.Schema(
        {probatio.Required("query", description="A few keywords, e.g. 'radon reading' or 'roof contractor'."): str}
    )
    annotations = READ_ONLY
    integration = DOMAIN

    def __init__(self, coordinator: WikiCoordinator) -> None:
        self.coordinator = coordinator

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> llm.ToolResult:
        hits = search(self.coordinator.data or [], tool_input.tool_args["query"])
        return llm.ToolResult(data={"results": hits} if hits else {"results": [], "note": "Nothing matched."})


class ReadTool(llm.Tool):
    """Read one page."""

    name = "read_house_wiki_page"
    description = (
        "Read a house wiki page by the name a search returned. For long pages (like the log), pass `find` to get "
        "only the sections that mention those words."
    )
    parameters = probatio.Schema(
        {
            probatio.Required("page", description="The page name or path from a search result."): str,
            probatio.Optional("find", description="Optional words to keep only the matching sections."): str,
        }
    )
    annotations = READ_ONLY
    integration = DOMAIN

    def __init__(self, coordinator: WikiCoordinator) -> None:
        self.coordinator = coordinator

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> llm.ToolResult:
        args: dict[str, Any] = tool_input.tool_args
        result = read(self.coordinator.data or [], args["page"], args.get("find"))
        return llm.ToolResult(data=result, error="error" in result)


class HouseWikiAPI(llm.API):
    """The tools, offered as one API that a conversation agent can be given."""

    def __init__(self, hass: HomeAssistant, coordinator: WikiCoordinator) -> None:
        super().__init__(hass=hass, id=DOMAIN, name="House wiki")
        self.coordinator = coordinator

    @override
    async def async_get_api_instance(self, llm_context: llm.LLMContext) -> llm.APIInstance:
        return llm.APIInstance(
            self, API_PROMPT, llm_context, tools=[SearchTool(self.coordinator), ReadTool(self.coordinator)]
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = WikiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(llm.async_register_api(hass, HouseWikiAPI(hass, coordinator)))
    entry.async_on_unload(entry.add_update_listener(_options_changed))
    return True


async def _options_changed(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
