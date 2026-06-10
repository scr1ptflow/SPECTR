import json
import os
import logging

logger = logging.getLogger(__name__)

CRITERIA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "bio_criteria.json",
)


class BioPredictor:
    def __init__(self):
        self._species = self._load_criteria()

    def _load_criteria(self):
        if not os.path.exists(CRITERIA_PATH):
            logger.warning(f"Bio criteria not found: {CRITERIA_PATH}")
            return []
        try:
            with open(CRITERIA_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load bio criteria: {e}")
            return []

    def predict(self, body_data):
        body_class = body_data.get("planet_class", "")
        temperature = body_data.get("temperature")
        atmosphere = body_data.get("atmosphere", "")
        gravity = body_data.get("gravity")
        volcanism = body_data.get("volcanism", "")

        matched = {}
        for sp in self._species:
            conditions = sp.get("conditions", {})

            if not self._check_planet_class(body_class, conditions):
                continue
            if not self._check_temperature(temperature, conditions):
                continue
            if not self._check_atmosphere(atmosphere, conditions):
                continue
            if not self._check_gravity(gravity, conditions):
                continue
            if not self._check_volcanism(volcanism, conditions):
                continue

            genus = sp.get("genus", "")
            reward = sp.get("reward", 0)
            if genus not in matched:
                matched[genus] = {"genus": genus, "reward_max": 0}
            if reward > matched[genus]["reward_max"]:
                matched[genus]["reward_max"] = reward

        return list(matched.values())

    def _check_planet_class(self, body_class, conditions):
        allowed = conditions.get("planet_classes")
        if not allowed:
            return True
        return body_class.lower() in {c.lower() for c in allowed}

    def _check_temperature(self, temperature, conditions):
        temp_cond = conditions.get("temperature")
        if not temp_cond:
            return True
        if temperature is None:
            return False
        t_min = temp_cond.get("min")
        t_max = temp_cond.get("max")
        if t_min is not None and temperature < t_min:
            return False
        if t_max is not None and temperature > t_max:
            return False
        return True

    def _check_atmosphere(self, atmosphere, conditions):
        allowed = conditions.get("atmospheres")
        if not allowed:
            return True
        if "Any" in allowed:
            return True
        if not atmosphere or atmosphere.lower() == "no atmosphere":
            return False
        for allowed_atm in allowed:
            if allowed_atm.lower() in atmosphere.lower():
                return True
        return False

    def _check_gravity(self, gravity, conditions):
        grav_cond = conditions.get("gravity")
        if not grav_cond:
            return True
        g_max = grav_cond.get("max")
        if g_max is not None:
            if gravity is None:
                return False
            if gravity > g_max:
                return False
        return True

    def _check_volcanism(self, volcanism, conditions):
        volc_required = conditions.get("volcanism")
        if volc_required is None:
            return True
        if not volcanism:
            return False
        volcanism_lower = volcanism.lower().strip()
        if volc_required is True:
            return bool(volcanism_lower)
        if isinstance(volc_required, str):
            return volc_required.lower() in volcanism_lower
        if isinstance(volc_required, list):
            return any(v.lower() in volcanism_lower for v in volc_required)
        return False
