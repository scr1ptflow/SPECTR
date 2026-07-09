from __future__ import annotations

import json
import time
import urllib.request
from typing import Optional

API_URL = "https://inara.cz/inapi/v1/"

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
    def __init__(self, api_key: str, cmdr_name: str, app_name: str = "SPECTR", app_version: str = "1.0"):
        self.api_key = api_key
        self.cmdr_name = cmdr_name
        self.app_name = app_name
        self.app_version = app_version
        self._profile_cache: Optional[dict] = None
        self._cached_cmdr: str = ""

    def _timestamp(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _request(self, events: list[dict]) -> Optional[dict]:
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
        except Exception:
            return None

    def get_commander_profile(self) -> Optional[dict]:
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
        self._profile_cache = profile
        self._cached_cmdr = self.cmdr_name
        return profile

    def get_ranks(self) -> dict[str, int]:
        profile = self.get_commander_profile()
        if not profile:
            return {}

        commander = profile.get("commander", {})
        inara_ranks = commander.get("commanderRanks", {})
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

        commander = profile.get("commander", {})
        inara_ranks = commander.get("commanderRanks", {})
        result: dict[str, int] = {}
        for inara_key, rank_data in inara_ranks.items():
            category = _INARA_RANK_MAP.get(inara_key)
            if category:
                result[category] = rank_data.get("progress", 0)
        return result

    def get_credits(self) -> Optional[int]:
        profile = self.get_commander_profile()
        if not profile:
            return None

        commander = profile.get("commander", {})
        return commander.get("commanderCredits")
