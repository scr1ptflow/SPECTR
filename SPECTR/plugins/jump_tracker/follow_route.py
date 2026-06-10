import os
import json
import logging

logger = logging.getLogger(__name__)

SCOOPABLE = {"O", "B", "A", "F", "G", "K", "M"}


class FollowRoute:
    def __init__(self, data_dir):
        self.name = ""
        self.hops = []
        self.active = False
        self.last_idx = -1
        self._routes_dir = os.path.join(data_dir, "routes")
        self._data_dir = data_dir
        self._mtime_map = {}
        os.makedirs(self._routes_dir, exist_ok=True)
        self._scan()

    def _scan(self):
        found = False

        try:
            for fname in sorted(os.listdir(self._routes_dir)):
                if not fname.endswith(".json"):
                    continue
                path = os.path.join(self._routes_dir, fname)
                try:
                    mtime = os.path.getmtime(path)
                    if self._mtime_map.get(path) == mtime:
                        continue
                    self._mtime_map[path] = mtime
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    hops_raw = data.get("hops", data.get("route", []))
                    if not hops_raw or len(hops_raw) < 2:
                        continue
                    found = True
                    self.name = data.get("name", fname.replace(".json", ""))
                    self.hops = []
                    for h in hops_raw:
                        hop = {
                            "name": h.get("system", h.get("name", "")),
                            "address": h.get("address", h.get("id64", 0)),
                            "star_class": h.get("star_class", h.get("class", "")),
                            "pos": (
                                h.get("pos") or
                                [h.get("x", 0), h.get("y", 0), h.get("z", 0)]
                            ),
                            "refuel": h.get("refuel", False),
                            "neutron": h.get("neutron", False),
                            "notes": h.get("notes", ""),
                        }
                        if hop["name"]:
                            self.hops.append(hop)
                    if len(self.hops) >= 2:
                        self.active = True
                        logger.info(f"Loaded FollowRoute '{self.name}' "
                                    f"({len(self.hops)} hops)")
                        break
                except (OSError, json.JSONDecodeError) as e:
                    logger.debug(f"Failed to load route {fname}: {e}")
        except OSError:
            pass

        if not found:
            self.active = False
            self.hops = []
            self.last_idx = -1
            self.name = ""

    def rescan(self):
        self._scan()

    def set_next(self, system_name):
        if not self.active or not system_name:
            return
        for i, hop in enumerate(self.hops):
            if hop["name"] == system_name:
                if self.last_idx < 0:
                    self.last_idx = i
                elif i == self.last_idx + 1:
                    self.last_idx = i
                break

    def remaining(self):
        if not self.active or self.last_idx < 0:
            return len(self.hops) - 1 if self.active else 0
        return max(0, len(self.hops) - self.last_idx - 1)

    def next_hop(self):
        if not self.active:
            return None
        idx = self.last_idx + 1
        return self.hops[idx] if idx < len(self.hops) else None

    def current_hop(self):
        if not self.active or self.last_idx < 0:
            return None
        return self.hops[self.last_idx] if self.last_idx < len(self.hops) else None

    def warnings(self, lookahead=3):
        if not self.active or self.last_idx < 0:
            return []
        result = []
        has_scoopable = False
        for i in range(self.last_idx + 1, min(len(self.hops), self.last_idx + 1 + lookahead)):
            h = self.hops[i]
            if h["neutron"]:
                result.append(("neutron", "Neutron boost ahead"))
            if h["refuel"]:
                result.append(("refuel", "Refuel recommended"))
            if h["star_class"] in SCOOPABLE:
                has_scoopable = True
        if not has_scoopable and self.remaining() > 0:
            next_h = self.next_hop()
            if next_h and next_h["star_class"] not in SCOOPABLE:
                if not any(s in next_h.get("notes", "").lower()
                           for s in ("scoop", "refuel", "fuel")):
                    result.append(("fuel", "No scoopable star soon"))
        return result

    def hop_notes(self):
        if not self.active or self.last_idx < 0:
            return ""
        hop = self.hops[self.last_idx] if self.last_idx < len(self.hops) else None
        if hop and hop["notes"]:
            return hop["notes"]
        return ""
