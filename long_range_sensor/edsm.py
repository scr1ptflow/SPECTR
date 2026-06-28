import json
import urllib.parse
import urllib.request
import urllib.error


class EdsmError(Exception):
    pass


USER_AGENT = "SPECTR-LongRangeSensor/0.1.0"


class EdsmClient:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def _get(self, base_url, endpoint, params=None):
        if params is None:
            params = {}
        if self.api_key:
            params["apiKey"] = self.api_key
        url = f"{base_url}/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise EdsmError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise EdsmError(f"Connection error: {e.reason}")

    def system_info(self, name):
        data = self._get("https://www.edsm.net/api-v1", "system", {
            "systemName": name,
            "showCoordinates": 1,
            "showInformation": 1,
        })
        if isinstance(data, dict) and data.get("name"):
            return data
        return None

    def sphere_systems(self, name, radius=120):
        data = self._get("https://www.edsm.net/api-v1", "sphere-systems", {
            "systemName": name,
            "radius": radius,
            "coords": 1,
        })
        return data if isinstance(data, list) else []

    def system_stations(self, name):
        data = self._get("https://www.edsm.net/api-system-v1", "stations", {
            "systemName": name,
            "showServices": 1,
        })
        if isinstance(data, dict) and "stations" in data:
            return data["stations"]
        return []
