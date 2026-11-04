"""Every 30 s: the aircraft round home from adsb.lol, paired with Flightradar24's flights, with owners and notable
aircraft added."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, EVENT_NOTABLE, FR24_SENSOR
from .data import match_aircraft, parse_alert_db, record

_LOGGER = logging.getLogger(__name__)

# adsb.lol: an unfiltered, free ADS-B network (it shows what owners ask Flightradar24 to block). The area is a
# little wider than Flightradar24's 8 km circle so a flight near its edge still finds its pair.
ADSB_POINT = "https://api.adsb.lol/v2/point/{lat:.4f}/{lon:.4f}/{nm}"
AREA_NM = 6
# adsbdb: registered owner by ICAO hex (registries such as the FAA's). Free; kept for a month per aircraft.
ADSBDB = "https://api.adsbdb.com/v0/aircraft/{hex}"
OWNER_TTL = 30 * 24 * 3600
OWNER_LOOKUPS_PER_POLL = 6
# plane-alert-db: a maintained public list of about 17,000 notable aircraft. Read again once a day.
ALERT_DB = "https://raw.githubusercontent.com/sdr-enthusiasts/plane-alert-db/main/plane-alert-db.csv"
ALERT_TTL = 24 * 3600
TIMEOUT = aiohttp.ClientTimeout(total=20)
HEADERS = {"User-Agent": "home-assistant-plane-details (github.com/ty496/ha-dashboard)"}


class PlaneDetailsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """The aircraft overhead, and what is known about each."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30), config_entry=entry)
        self._session = async_get_clientsession(hass)
        self._owner_store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.owners")
        self._owners: dict[str, dict[str, Any]] | None = None
        self._alerts: dict[str, dict[str, Any]] = {}
        self._alerts_at = 0.0
        self._notable_seen: set[str] = set()

    async def _get_json(self, url: str) -> Any:
        async with self._session.get(url, headers=HEADERS, timeout=TIMEOUT) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def _refresh_alerts(self) -> None:
        if self._alerts and time.time() - self._alerts_at < ALERT_TTL:
            return
        try:
            async with self._session.get(ALERT_DB, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("plane-alert-db not read (%s); trying again next poll", err)
            return
        self._alerts = await self.hass.async_add_executor_job(parse_alert_db, text)
        self._alerts_at = time.time()
        _LOGGER.info("plane-alert-db: %d aircraft", len(self._alerts))

    async def _owner(self, hexcode: str, budget: list[int]) -> dict[str, Any] | None:
        if self._owners is None:
            self._owners = await self._owner_store.async_load() or {}
        have = self._owners.get(hexcode)
        if have and time.time() - have.get("at", 0) < OWNER_TTL:
            return have
        if budget[0] <= 0:
            return have
        budget[0] -= 1
        try:
            body = await self._get_json(ADSBDB.format(hex=hexcode))
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("adsbdb %s: %s", hexcode, err)
            return have
        found = body.get("response") if isinstance(body, dict) else None
        plane = found.get("aircraft") if isinstance(found, dict) else None
        self._owners[hexcode] = {
            "owner": (plane or {}).get("registered_owner") or "",
            "country": (plane or {}).get("registered_owner_country_name") or "",
            "at": time.time(),
        }
        self._owner_store.async_delay_save(lambda: self._owners or {}, 30)
        return self._owners[hexcode]

    async def _async_update_data(self) -> dict[str, Any]:
        home = (self.hass.config.latitude, self.hass.config.longitude)
        await self._refresh_alerts()
        try:
            body = await self._get_json(ADSB_POINT.format(lat=home[0], lon=home[1], nm=AREA_NM))
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"adsb.lol: {err}") from err
        aircraft = [a for a in (body.get("ac") or []) if a.get("hex") and not str(a["hex"]).startswith("~")]

        state = self.hass.states.get(FR24_SENSOR)
        flights = (state.attributes.get("flights") if state else None) or []
        paired: dict[str, dict[str, Any]] = {}
        for f in flights:
            a = match_aircraft(f, aircraft)
            if a is not None and f.get("id"):
                paired[str(f["id"])] = a

        # Owners for the aircraft Flightradar24 is showing first, a few lookups a poll.
        budget = [OWNER_LOOKUPS_PER_POLL]
        wanted = list(paired.values()) + [a for a in aircraft if a not in paired.values()]
        records: dict[str, dict[str, Any]] = {}
        for a in wanted:
            hexcode = str(a["hex"]).upper()
            if hexcode in records:
                continue
            owner = await self._owner(hexcode, budget)
            records[hexcode] = record(a, owner, self._alerts.get(hexcode), home)

        by_fr24 = {fid: records[str(a["hex"]).upper()] for fid, a in paired.items()}
        notable = [r for r in records.values() if r["poi"]]
        for r in notable:
            if r["hex"] not in self._notable_seen:
                self.hass.bus.async_fire(EVENT_NOTABLE, r)
        self._notable_seen = {r["hex"] for r in notable}
        return {
            "aircraft": sorted(records.values(), key=lambda r: r["distance"] if r["distance"] is not None else 1e9),
            "by_fr24": by_fr24,
            "notable": notable,
        }
