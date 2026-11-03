"""Keeps the in-scope wiki pages in memory, refreshed from GitHub every 30 minutes (only changed files are fetched)."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
from .wiki import Page, Scope, make_page, split_list

_LOGGER = logging.getLogger(__name__)

API = "https://api.github.com"
TIMEOUT = aiohttp.ClientTimeout(total=30)


def github_headers(token: str, raw: bool = False) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "home-assistant-house-wiki",
    }


def entry_scope(entry: ConfigEntry) -> Scope:
    opts = entry.options
    return Scope(
        include=split_list(opts.get(CONF_INCLUDE, DEFAULT_INCLUDE)),
        mention_in=split_list(opts.get(CONF_MENTION_IN, DEFAULT_MENTION_IN)),
        mention_terms=split_list(opts.get(CONF_MENTION_TERMS, DEFAULT_MENTION_TERMS)),
        exclude=split_list(opts.get(CONF_EXCLUDE, DEFAULT_EXCLUDE)),
    )


class WikiCoordinator(DataUpdateCoordinator[list[Page]]):
    """Pages in scope, newest copy from the repo's branch."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=timedelta(minutes=30))
        self._files: dict[str, tuple[str, str]] = {}  # path -> (blob sha, text)

    async def _async_update_data(self) -> list[Page]:
        entry = self.config_entry
        session = async_get_clientsession(self.hass)
        token, repo = entry.data[CONF_TOKEN], entry.data[CONF_REPO]
        branch = entry.data.get(CONF_BRANCH, DEFAULT_BRANCH)
        scope = entry_scope(entry)
        try:
            async with session.get(
                f"{API}/repos/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
                headers=github_headers(token),
                timeout=TIMEOUT,
            ) as resp:
                if resp.status in (401, 403, 404):
                    raise UpdateFailed(f"GitHub answered {resp.status} for {repo}: check the token and repo name")
                resp.raise_for_status()
                tree = await resp.json()
            wanted = {
                item["path"]: item["sha"]
                for item in tree.get("tree", [])
                if item.get("type") == "blob" and scope.candidate(item["path"])
            }
            changed = [path for path, sha in wanted.items() if self._files.get(path, ("",))[0] != sha]
            gate = asyncio.Semaphore(6)

            async def fetch(path: str) -> None:
                async with gate, session.get(
                    f"{API}/repos/{repo}/git/blobs/{wanted[path]}",
                    headers=github_headers(token, raw=True),
                    timeout=TIMEOUT,
                ) as resp:
                    resp.raise_for_status()
                    self._files[path] = (wanted[path], (await resp.read()).decode("utf-8", "replace"))

            await asyncio.gather(*(fetch(path) for path in changed))
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"GitHub fetch failed: {err}") from err
        for path in [p for p in self._files if p not in wanted]:
            del self._files[path]
        pages = [make_page(path, text) for path, (_, text) in sorted(self._files.items()) if scope.keeps(path, text)]
        _LOGGER.debug("House wiki: %d pages in scope (%d fetched)", len(pages), len(changed))
        return pages
