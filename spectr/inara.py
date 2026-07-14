# Inara.cz API client — fetches commander profile data from the Inara
# vertical slice API (/inapi/v1/).
#
# Can provide rank data as a fallback when the game journal doesn't have it
# (e.g. if the journal files have been cleared).
#
# API docs: https://inara.cz/inapi/
#
# Usage:
#     client = InaraClient(api_key="...", cmdr_name="Cmdr Name")
#     profile = client.get_commander_profile()
#     ranks = client.get_ranks()

from __future__ import annotations

import json
import logging
import time
import urllib.request

log = logging.getLogger(__name__)

API_URL = "https://inara.cz/inapi/v1/"

# Maps Inara's rank category keys to the internal category names used in
# the journal parser. "mercenary" is an alias for "soldier" in Inara's data.
_INARA_RANK_MAP = {
    "combat": "Combat",
    "trade": "Trade",
    "explore": "Explore",
    "cqc": "CQC",
    "empire": "Empire",
    "federation": "Federation",
    "soldier": "Soldier",
    "mercenary": "Soldier",
    "exobiologist": "Exobiologist",
}


class InaraClient:
    """Lightweight client for the Inara API.

    Results are cached per commander name to avoid repeated network calls
    during a single session.
    """

    def __init__(
        self,
        api_key: str,
        cmdr_name: str,
        app_name: str = "SPECTR",
        app_version: str = "1.0",
    ):
        self.api_key = api_key
        self.cmdr_name = cmdr_name
        self.app_name = app_name
        self.app_version = app_version
        self._profile_cache: dict | None = None
        self._cached_cmdr: str = ""

    def _timestamp(self) -> str:
        """ISO-8601 timestamp for the API request header."""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _request(self, events: list[dict]) -> dict | None:
        """Send a POST request to the Inara API and return the response.

        The payload follows the Inara API spec:
          header  — appName, appVersion, APIkey, commanderName
          events  — list of event objects (each with eventName, etc.)
        """
        payload = {
            "header": {
                "appName": self.app_name,
                "appVersion": self.app_version,
                "APIkey": self.api_key,
                "commanderName": self.cmdr_name,
            },
            "events": events,
        }

        try:
            data = json.dumps(payload, separators=(",", ":")).encode()
            req = urllib.request.Request(
                API_URL,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            log.warning("Inara API request failed: %s", exc)
            return None

    def get_commander_profile(self) -> dict | None:
        """Fetch the full commander profile from Inara.

        Returns the "commander" sub-dict on success, or None on error.
        Results are cached so repeated calls in the same session are free.
        """
        if self._cached_cmdr == self.cmdr_name and self._profile_cache is not None:
            return self._profile_cache

        result = self._request([
            {
                "eventName": "getCommanderProfile",
                "eventTimestamp": self._timestamp(),
                "eventData": {"searchName": self.cmdr_name},
            }
        ])

        if not isinstance(result, dict):
            return None

        header = result.get("header", {})
        if header.get("eventStatus") != 1:
            return None

        events = result.get("events", [])
        if not events:
            return None

        profile = events[0].get("eventData", {})
        if not isinstance(profile, dict):
            return None

        # Inara wraps profile data in {"commander": {...}} sometimes
        if "commander" in profile:
            profile = profile["commander"]

        self._profile_cache = profile
        self._cached_cmdr = self.cmdr_name
        return profile

    # --- Typed convenience getters ---

    def get_ranks(self) -> dict[str, int]:
        profile = self.get_commander_profile()
        if not profile:
            return {}

        inara_ranks = profile.get("commanderRanks", {})
        result: dict[str, int] = {}
        for inara_key, rank_data in inara_ranks.items():
            category = _INARA_RANK_MAP.get(inara_key)
            if category:
                result[category] = rank_data.get("rank", 0)
        return result

    def get_rank_progress(self) -> dict[str, int]:
        profile = self.get_commander_profile()
        if not profile:
            return {}

        inara_ranks = profile.get("commanderRanks", {})
        result: dict[str, int] = {}
        for inara_key, rank_data in inara_ranks.items():
            category = _INARA_RANK_MAP.get(inara_key)
            if category:
                result[category] = rank_data.get("progress", 0)
        return result

    def get_all_ranks(self) -> dict[str, dict]:
        """Return the raw commanderRanks dict for advanced inspection."""
        profile = self.get_commander_profile()
        if not profile:
            return {}
        ranks = profile.get("commanderRanks", {})
        if isinstance(ranks, dict):
            return ranks
        return {}

    def get_achievements(self) -> list[dict]:
        profile = self.get_commander_profile()
        if not profile:
            return []
        return profile.get("commanderAchievements", [])

    def get_squadron(self) -> dict | None:
        profile = self.get_commander_profile()
        if not profile:
            return None
        return profile.get("commanderSquadron")

    def get_credits(self) -> int | None:
        profile = self.get_commander_profile()
        if not profile:
            return None
        return profile.get("commanderCredits")
