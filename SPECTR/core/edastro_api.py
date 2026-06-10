import time
import urllib.request
import urllib.parse
import json
import os
import logging
from core.threads import submit as _api_submit

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


class EdastroApi:
    BASE = "https://edastro.com"

    def __init__(self):
        self._cache = {}
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._cache_path = os.path.join(CACHE_DIR, "edastro_cache.json")
        self._load_cache()

    def _load_cache(self):
        path = self._cache_path
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except OSError as e:
            logger.warning(f"Failed to save EDAstro cache: {e}")

    def _fetch(self, url, cache_key, ttl=300, callback=None):
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and (now - cached.get("_ts", 0)) < ttl:
            if callback:
                callback(cached.get("data"))
            return
        _api_submit(self._do_fetch, url, cache_key, ttl, callback)

    def _do_fetch(self, url, cache_key, ttl, callback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SPECTR/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            self._cache[cache_key] = {"data": data, "_ts": time.time()}
            self._save_cache()
            if callback:
                callback(data)
        except Exception as e:
            logger.debug(f"EDAstro fetch failed: {e}")
            if callback:
                callback(None)

    def fetch_system(self, system_name, callback=None):
        name = (system_name or "").strip()
        if not name:
            return
        url = f"{self.BASE}/api/starsystem?q={urllib.parse.quote(name)}"
        self._fetch(url, f"system:{name.lower()}", ttl=600, callback=callback)

    def fetch_systems_batch(self, names, callback=None):
        if not names:
            return
        batch = [n.strip() for n in names[:10] if n.strip()]
        if not batch:
            return
        query = ",".join(urllib.parse.quote(n) for n in batch)
        cache_key = "systems:" + ",".join(sorted(n.lower() for n in batch))
        url = f"{self.BASE}/api/starsystem?q={query}"
        self._fetch(url, cache_key, ttl=600, callback=callback)

    def fetch_gec_all(self, callback=None):
        url = f"{self.BASE}/gec/json/all"
        self._fetch(url, "gec:all", ttl=900, callback=callback)

    def fetch_gec_combined(self, callback=None):
        url = f"{self.BASE}/gec/json/combined"
        self._fetch(url, "gec:combined", ttl=900, callback=callback)

    def fetch_gec_rare(self, callback=None):
        url = f"{self.BASE}/gec/json/rare"
        self._fetch(url, "gec:rare", ttl=900, callback=callback)

    def fetch_gec_single(self, poi_id, callback=None):
        url = f"{self.BASE}/gec/json/single/{poi_id}"
        self._fetch(url, f"gec:single:{poi_id}", ttl=900, callback=callback)

    def fetch_gec_by_id64(self, id64, callback=None):
        url = f"{self.BASE}/gec/json/id64/{id64}"
        self._fetch(url, f"gec:id64:{id64}", ttl=900, callback=callback)

    def fetch_gec_nearest(self, x, y, z, min_rating=None, callback=None):
        path = f"{x}/{y}/{z}"
        if min_rating is not None:
            path += f"/{min_rating}"
        url = f"{self.BASE}/gec/json/nearest/{path}"
        self._fetch(url, f"gec:nearest:{x},{y},{z},{min_rating}", ttl=300, callback=callback)

    def fetch_gec_categories(self, callback=None):
        url = f"{self.BASE}/gec/json/categories"
        self._fetch(url, "gec:categories", ttl=3600, callback=callback)

    def fetch_gec_stats(self, callback=None):
        url = f"{self.BASE}/gec/json/stats"
        self._fetch(url, "gec:stats", ttl=3600, callback=callback)
