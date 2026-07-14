from __future__ import annotations

import json
import logging
import urllib.request
import urllib.parse

log = logging.getLogger(__name__)

BASE_URL = "https://www.edsm.net"


class EDSMClient:
    """Lightweight client for the EDSM API.

    API docs: https://www.edsm.net/en/api-system-v1
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._cache: dict = {}

    def _get(self, path: str, params: dict | None = None) -> dict | None:
        url = f"{BASE_URL}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        if url in self._cache:
            return self._cache[url]

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SPECTR/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                self._cache[url] = data
                return data
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            log.warning("EDSM API request failed: %s", exc)
            return None

    def get_nearby_systems(
        self, system_name: str, radius_ly: int = 50, max_results: int = 100
    ) -> list[dict]:
        """Find systems within *radius_ly* light years of *system_name*."""
        data = self._get(
            "/api-v1/sphere-systems",
            {
                "systemName": system_name,
                "radius": radius_ly,
                "onlyRadius": 1,
                "limit": max_results,
            },
        )
        if not data:
            return []
        return data if isinstance(data, list) else []

    def get_stations(self, system_name: str) -> list[dict]:
        """Get all stations in *system_name*."""
        data = self._get(
            "/api-system-v1/stations",
            {"systemName": system_name},
        )
        if not data or not isinstance(data, dict):
            return []
        return data.get("stations", [])

    def get_system_details(self, system_name: str) -> dict | None:
        """Get full system details including bodies."""
        data = self._get(
            "/api-system-v1/bodies",
            {"systemName": system_name},
        )
        return data


# Ship internal name → landing pad size ("S"=small, "M"=medium, "L"=large).
# Small pads fit S ships, medium fits S+M, large fits S+M+L.
_SHIP_PAD_SIZE: dict[str, str] = {
    "sidewinder": "S",
    "eagle": "S",
    "empire_eagle": "S",
    "hauler": "S",
    "adder": "S",
    "viper": "S",
    "viper_mkiii": "S",
    "viper_mkiv": "S",
    "cobramkiii": "S",
    "cobra_mkiii": "S",
    "cobramkiv": "S",
    "cobra_mkiv": "S",
    "cobra_mk_v": "S",
    "diamondback": "S",
    "dbs": "S",
    "asp_scout": "S",
    "vulture": "S",

    "type6": "M",
    "type7": "M",
    "type8": "M",
    "keelback": "M",
    "dolphin": "M",
    "ferdelance": "M",
    "mamba": "M",
    "python": "M",
    "python_nx": "M",
    "krait_mkii": "M",
    "krait_light": "M",
    "diamondbackxl": "M",
    "dbx": "M",
    "asp": "M",
    "federation_dropship": "M",
    "federation_dropship_mkii": "M",
    "federation_gunship": "M",
    "alliance_chieftain": "M",
    "alliance_challenger": "M",
    "alliance_crusader": "M",
    "empire_courier": "M",
    "mandalay": "M",
    "corsair": "M",
    "kestrel": "M",

    "type9": "L",
    "type9_military": "L",
    "type10": "L",
    "type11": "L",
    "belugaliner": "L",
    "beluga": "L",
    "orca": "L",
    "anaconda": "L",
    "federation_corvette": "L",
    "cutter": "L",
    "empire_trader": "L",
    "panther_mk2": "L",
    "explorer_nx": "L",
    "lynx": "L",
}


def get_pad_size(ship_type_internal: str) -> str:
    """Return the landing pad size letter for *ship_type_internal*.

    Returns "S", "M", or "L". Defaults to "L" if the ship is unknown.
    """
    key = ship_type_internal.lower().replace(" ", "")
    return _SHIP_PAD_SIZE.get(key, "L")


def pad_compatible(station_max_pads: str, ship_pad_size: str) -> bool:
    """Return True if *station_max_pads* can accommodate *ship_pad_size*."""
    hierarchy = {"S": 1, "M": 2, "L": 3}
    return hierarchy.get(station_max_pads, 3) >= hierarchy.get(ship_pad_size, 1)
