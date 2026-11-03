"""CalDAV edit: change and delete events in CalDAV calendars (2026-11-03).

Home Assistant's CalDAV calendars can only create events. This adds caldav_edit.update_event and
caldav_edit.delete_event. Each reuses the calendar entity's own caldav connection, so there is no second login,
and the exact calendar behind the entity is used even when two calendars share a name ("Home" twice in iCloud).
The matching and editing rules live in events.py.
"""

from __future__ import annotations

from functools import partial
from typing import Any

from caldav.lib.error import DAVError
from caldav.lib.http_sync import requests as caldav_requests
import probatio

from homeassistant.components.calendar.const import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from . import events
from .const import (
    ATTR_DATE,
    ATTR_NEW_DESCRIPTION,
    ATTR_NEW_END,
    ATTR_NEW_LOCATION,
    ATTR_NEW_START,
    ATTR_NEW_TITLE,
    ATTR_TITLE,
    DOMAIN,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

FIND_SCHEMA = {
    probatio.Required(ATTR_ENTITY_ID): cv.entity_ids,
    probatio.Required(ATTR_DATE): cv.date,
    probatio.Required(ATTR_TITLE): cv.string,
}
DELETE_SCHEMA = probatio.Schema(FIND_SCHEMA)
UPDATE_SCHEMA = probatio.Schema(
    {
        **FIND_SCHEMA,
        probatio.Optional(ATTR_NEW_TITLE): cv.string,
        probatio.Optional(ATTR_NEW_START): cv.string,
        probatio.Optional(ATTR_NEW_END): cv.string,
        probatio.Optional(ATTR_NEW_LOCATION): cv.string,
        probatio.Optional(ATTR_NEW_DESCRIPTION): cv.string,
    }
)

NETWORK_ERRORS = (caldav_requests.exceptions.ConnectionError, caldav_requests.exceptions.Timeout, DAVError)


def _calendars(hass: HomeAssistant, entity_ids: list[str]) -> tuple[list[tuple[Any, str]], list[Any]]:
    """The caldav Calendar and display name behind each entity, plus the entities (to refresh afterwards)."""
    component = hass.data.get(DATA_COMPONENT)
    found, entities = [], []
    for entity_id in entity_ids:
        entity = component.get_entity(entity_id) if component else None
        calendar = getattr(getattr(entity, "coordinator", None), "calendar", None)
        if calendar is None:
            raise ServiceValidationError(f"{entity_id} is not a CalDAV calendar")
        state = hass.states.get(entity_id)
        found.append((calendar, state.name if state else entity_id))
        entities.append(entity)
    return found, entities


async def _run(hass: HomeAssistant, call: ServiceCall, action: str) -> ServiceResponse:
    calendars, entities = _calendars(hass, call.data[ATTR_ENTITY_ID])
    tz = dt_util.get_default_time_zone()

    def work() -> dict[str, str]:
        copies = events.find(calendars, call.data[ATTR_DATE], call.data[ATTR_TITLE], tz)
        if action == "delete":
            return events.delete(copies, tz)
        return events.update(
            copies,
            tz,
            new_title=call.data.get(ATTR_NEW_TITLE),
            new_start=call.data.get(ATTR_NEW_START),
            new_end=call.data.get(ATTR_NEW_END),
            new_location=call.data.get(ATTR_NEW_LOCATION),
            new_description=call.data.get(ATTR_NEW_DESCRIPTION),
        )

    try:
        result = await hass.async_add_executor_job(work)
    except events.EventError as err:
        raise ServiceValidationError(str(err)) from err
    except NETWORK_ERRORS as err:
        raise HomeAssistantError(f"CalDAV {action} error: {err}") from err
    for entity in entities:
        hass.async_create_task(entity.coordinator.async_request_refresh())
    return {("deleted" if action == "delete" else "updated"): result}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the actions."""
    hass.services.async_register(
        DOMAIN,
        "update_event",
        partial(_run, hass, action="update"),
        schema=UPDATE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "delete_event",
        partial(_run, hass, action="delete"),
        schema=DELETE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nothing to set up per entry; the entry only makes Home Assistant load the integration."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
