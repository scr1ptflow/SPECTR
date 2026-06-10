import math
import logging

logger = logging.getLogger(__name__)

DOCKED          = 1 << 0
LANDED          = 1 << 1
LANDING_GEAR    = 1 << 2
SHIELDS_UP      = 1 << 3
SUPERCRUISE     = 1 << 4
FLIGHT_ASSIST   = 1 << 5
HARDPOINTS      = 1 << 6
IN_WING         = 1 << 7
LIGHTS_ON       = 1 << 8
CARGO_SCOOP     = 1 << 9
SILENT_RUNNING  = 1 << 10
SCOOPING_FUEL   = 1 << 11
SRV_HANDBRAKE   = 1 << 12
SRV_TURRET      = 1 << 13
SRV_UNDER_SHIP  = 1 << 14
SRV_DRIVE_ASSIST = 1 << 15
FSD_MASS_LOCKED = 1 << 16
FSD_CHARGING    = 1 << 17
FSD_COOLDOWN    = 1 << 18
LOW_FUEL        = 1 << 19
OVER_HEATING    = 1 << 20
HAS_LAT_LONG    = 1 << 21
IN_DANGER       = 1 << 22
BEING_INTERDICTED = 1 << 23
IN_MAIN_SHIP    = 1 << 24
IN_FIGHTER      = 1 << 25
IN_SRV          = 1 << 26
ANALYSIS_MODE   = 1 << 27
NIGHT_VISION    = 1 << 28
ALTITUDE_AVG    = 1 << 29
FSD_JUMP        = 1 << 30
SRV_HIGH_BEAM   = 1 << 31

ON_FOOT         = 1 << 32
IN_TAXI         = 1 << 33
IN_MULTICREW    = 1 << 34
ON_FOOT_STATION = 1 << 35
ON_FOOT_PLANET  = 1 << 36
AIM_DOWN_SIGHT  = 1 << 37
LOW_OXYGEN      = 1 << 38
LOW_HEALTH      = 1 << 39
COLD            = 1 << 40
HOT             = 1 << 41
VERY_COLD       = 1 << 42
VERY_HOT        = 1 << 43
GLIDING         = 1 << 44
ON_FOOT_HANGAR  = 1 << 45
ON_FOOT_SOCIAL  = 1 << 46
ON_FOOT_EXTERIOR = 1 << 47
BREATHABLE_ATMO = 1 << 48
TELEPRESENCE    = 1 << 49
PHYSICAL_MC     = 1 << 50
FSS_MODE        = 1 << 51

GUI_FOCUS = {
    0: "None",
    1: "InternalPanel",
    2: "ExternalPanel",
    3: "CommsPanel",
    4: "RolePanel",
    5: "StationServices",
    6: "GalaxyMap",
    7: "SystemMap",
    8: "Orrery",
    9: "FSSMode",
    10: "SAAView",
    11: "Codex",
}


class Status:
    def __init__(self):
        self.flags = 0
        self.flags2 = 0
        self.fuel_main = 0.0
        self.fuel_capacity = 0.0
        self.cargo = 0.0
        self.latitude = None
        self.longitude = None
        self.heading = None
        self.altitude = None
        self.oxygen = None
        self.health = None
        self.temperature = None
        self.selected_weapon = None
        self.gravity = None
        self.planet_radius = None
        self.body_name = None
        self.balance = None
        self.gui_focus = 0

    def update(self, data):
        self.flags = data.get("Flags", self.flags)
        self.flags2 = data.get("Flags2", self.flags2)
        self.fuel_main = self._nget(data, ["Fuel", "FuelMain"], self.fuel_main)
        self.fuel_capacity = self._nget(data, ["Fuel", "FuelCapacity"], self.fuel_capacity)
        self.cargo = self._nget(data, ["Cargo"], self.cargo)
        self.latitude = self._nget(data, ["Latitude"], self.latitude)
        self.longitude = self._nget(data, ["Longitude"], self.longitude)
        self.heading = self._nget(data, ["Heading"], self.heading)
        self.altitude = self._nget(data, ["Altitude"], self.altitude)
        self.oxygen = self._nget(data, ["Oxygen"], self.oxygen)
        self.health = self._nget(data, ["Health"], self.health)
        self.temperature = self._nget(data, ["Temperature"], self.temperature)
        self.selected_weapon = data.get("SelectedWeapon", self.selected_weapon)
        self.gravity = self._nget(data, ["Gravity"], self.gravity)
        self.planet_radius = self._nget(data, ["PlanetRadius"], self.planet_radius)
        self.body_name = data.get("BodyName", self.body_name)
        self.balance = data.get("Balance", self.balance)
        self.gui_focus = data.get("GuiFocus", self.gui_focus)

    def _nget(self, data, keys, default):
        d = data
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
                if d is None:
                    return default
            else:
                return default
        return d

    def is_docked(self):
        return bool(self.flags & DOCKED)

    def is_landed(self):
        return bool(self.flags & LANDED)

    def is_supercruise(self):
        return bool(self.flags & SUPERCRUISE)

    def is_in_ship(self):
        return bool(self.flags & IN_MAIN_SHIP)

    def is_in_fighter(self):
        return bool(self.flags & IN_FIGHTER)

    def is_in_srv(self):
        return bool(self.flags & IN_SRV)

    def is_on_foot(self):
        return bool(self.flags & ON_FOOT)

    def is_in_fss(self):
        return bool(self.flags & FSS_MODE)

    def is_in_dss(self):
        return bool(self.flags & ANALYSIS_MODE) and bool(self.flags & HAS_LAT_LONG)

    def is_analysis_mode(self):
        return bool(self.flags & ANALYSIS_MODE)

    def has_lat_long(self):
        return bool(self.flags & HAS_LAT_LONG)

    def get_mode(self):
        if self.is_on_foot():
            return "OnFoot"
        if self.is_in_srv():
            return "InSrv"
        if self.is_in_fighter():
            return "Fighter"
        if self.is_supercruise():
            return "Supercruise"
        if self.is_docked():
            return "Docked"
        if self.is_landed():
            return "Landed"
        if self.is_in_ship():
            return "InShip"
        return "Unknown"

    def gui_focus_name(self):
        return GUI_FOCUS.get(self.gui_focus, f"Unknown({self.gui_focus})")

    def bearing_to(self, lat, lon):
        if self.latitude is None or self.longitude is None:
            return None
        d_lon = math.radians(lon - self.longitude)
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(lat)
        y = math.sin(d_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def distance_to(self, lat, lon):
        if self.latitude is None or self.longitude is None or self.planet_radius is None:
            return None
        d_lat = math.radians(lat - self.latitude)
        d_lon = math.radians(lon - self.longitude)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(self.latitude)) *
             math.cos(math.radians(lat)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return c * self.planet_radius

    def heading_diff(self, target_bearing):
        if self.heading is None or target_bearing is None:
            return None
        diff = (target_bearing - self.heading + 180) % 360 - 180
        return diff
