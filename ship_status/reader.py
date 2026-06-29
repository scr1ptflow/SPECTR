import json
import os
import glob
import re

from blackbox.formatter import print_progress
from webui._utils import find_journal_dir, get_latest_journal

_COMMODITY_PRICES = {
    # Minerals
    "painite": 520000, "platinum": 230000, "osmium": 65000,
    "gold": 9500, "silver": 4800, "palladium": 14000,
    "bertrandite": 25000, "indite": 15000, "gallite": 14000,
    "coltan": 6000, "uraninite": 5000, "lepidolite": 3500,
    "monazite": 720000, "musgravite": 300000, "alexandrite": 280000,
    "grandidierite": 270000, "rhodplumsite": 720000, "serendibite": 310000,
    "benitoite": 750000, "low temperature diamonds": 950000,
    "void opals": 700000,
    "bromellite": 4500, "methanol monohydrate": 2500,
    "hydrogen peroxide": 3500, "liquid oxygen": 2500,
    "mineral oil": 1500, "surface stabilisers": 2000,
    "synthetic reagents": 8000, "tritium": 50000,
    # Metals
    "copper": 1200, "aluminium": 600, "steel": 1300,
    "titanium": 1500, "tantalum": 4000, "niobium": 2500,
    "beryllium": 8500, "cobalt": 2500, "indium": 6000,
    "lithium": 1800, "molybdenum": 2500, "ruthenium": 55000,
    "technetium": 55000, "thorium": 12000, "uranium": 3500,
    "gallium": 5000, "hafnium 178": 70000, "samarium": 5000,
    "thallium": 4000, "vanadium": 2000,
    # Technology / Manufactured
    "computer components": 1200, "consumer technology": 7000,
    "hazardous environment suits": 700, "resonating separators": 8000,
    "structural regulators": 3000, "telemetry suite": 4000,
    "building fabricators": 2500, "power generators": 3500,
    "water purifiers": 1500, "military grade fabrics": 2000,
    "advanced medicines": 2000, "basic medicines": 600,
    "performance enhancers": 7000,
    # Agricultural
    "grain": 600, "tea": 2000, "coffee": 1700,
    "fish": 1200, "fruit and vegetables": 700,
    "animal meat": 1500, "food cartridges": 400,
    "synthetic meat": 600, "algae": 400,
    # Industrial
    "polymers": 900, "semiconductors": 1500,
    "superconductors": 7000, "ceramic composites": 1500,
    "cmm composite": 1500,
    "insulating membrane": 11000, "micro-weave cooling hoses": 2000,
    "neofabric insulation": 6000, "emergency power cells": 2000,
    "power transfer bus": 3000, "radiation baffle": 2500,
    "reinforced mounting plate": 2000, "hn shock mount": 1000,
    # Rare goods
    "onionhead": 10000, "lavian brandy": 11000,
    # Disposables / no value
    "limpet": 0, "drones": 0,
    "occupied cryo pod": 0, "escape pod": 0,
    "unknown artifact": 0, "ancient artefact": 0,
}


CORE_SLOTS = {
    "Armour": "Bulkheads",
    "PowerPlant": "Power Plant",
    "MainEngines": "Thrusters",
    "FrameShiftDrive": "Frame Shift Drive",
    "LifeSupport": "Life Support",
    "PowerDistributor": "Power Distributor",
    "Radar": "Sensors",
    "FuelTank": "Fuel Tank",
    "PlanetaryApproachSuite": "Planetary Approach Suite",
    "CargoHatch": "Cargo Hatch",
}

HARDPOINT_PREFIXES = (
    "SmallHardpoint", "MediumHardpoint", "LargeHardpoint", "HugeHardpoint",
    "SmallMiningHardpoint", "MediumMiningHardpoint", "LargeMiningHardpoint",
)
UTILITY_PREFIX = "TinyHardpoint"

OPTIONAL_PREFIXES = ("Slot", "LimpetController")

_KNOWN_SHIPS = {
    "explorer_nx": "Asp Explorer",
    "lakonminer": "Lakon Type-11 Prospector",
    "indep_courier": "Imperial Courier",
}

_ITEM_KNOWN = {
    "modularcargobaydoor": "Cargo Hatch",
    "int_multidronecontrol_miningv2_size5_class5": "Multi-limpet Controller",
    "hpt_miningtoolv2_fixed_large": "Mining Volley Repeater",
    "int_dronecontrol_prospector_size1_class5": "Prospector Controller",
    "int_planetapproachsuite_advanced": "Planetary Approach Suite",
    "int_dockingcomputer_advanced": "Docking Computer",
    "int_detailedsurfacescanner_tiny": "Surface Scanner",
    "int_supercruiseassist": "Supercruise Assist",
    "int_guardianfsdbooster_size5": "Guardian FSD Booster",
    "int_shieldgenerator_size5_class2": "Shield Generator",
    "int_shieldgenerator_size3_class2": "Shield Generator",
    "int_fuelscoop_size7_class5": "Fuel Scoop",
    "int_repairer_size5_class5": "Repair Limpet Controller",
    "int_repairer_size4_class5": "Repair Limpet Controller",
    "int_buggybay_size2_class2": "SRV Bay",
    "int_cargorack_size6_class1": "Cargo Rack",
    "int_cargorack_size5_class1": "Cargo Rack",
    "int_cargorack_size4_class1": "Cargo Rack",
    "int_refinery_size4_class5": "Refinery",
    "int_dronecontrol_repair_size3_class2": "Repair Controller",
}

_SLOT_NAMES = {
    "Armour": "Bulkheads",
    "PowerPlant": "Power Plant",
    "MainEngines": "Thrusters",
    "FrameShiftDrive": "Frame Shift Drive",
    "LifeSupport": "Life Support",
    "PowerDistributor": "Power Distributor",
    "Radar": "Sensors",
    "FuelTank": "Fuel Tank",
    "PlanetaryApproachSuite": "Planetary Approach Suite",
    "CargoHatch": "Cargo Hatch",
    "VesselVoice": "Voice Pack",
    "ShipCockpit": "Cockpit",
}


def _clean_item_name(item_id: str) -> str:
    lowered = item_id.lower()
    if lowered in _ITEM_KNOWN:
        return _ITEM_KNOWN[lowered]

    raw = item_id
    for prefix in ("hpt_", "int_", "paintjob_", "decal_", "voicepack_", "explorer_", "lakonminer_", "armour_"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break

    parts = raw.split("_")
    filtered = []
    for p in parts:
        if p.startswith(("size", "class", "grade")) or p.isdigit():
            continue
        if p in ("default", "advanced", "standard", "basic"):
            continue
        filtered.append(p.capitalize())

    if not filtered:
        return item_id
    return " ".join(filtered)


_CLASS_TO_RATING = {"1": "E", "2": "D", "3": "C", "4": "B", "5": "A"}

def _module_rating(m: dict) -> str | None:
    item = m.get("Item", "")
    slot = m.get("Slot", "")

    if slot == "Armour":
        localised = m.get("Module_Localised") or m.get("Item_Localised") or ""
        if localised:
            return None

        lowered = item.lower()

        # bulkhead type keywords found anywhere in the Item
        keywords = [
            ("lightweight", "Lightweight"),
            ("reinforced", "Reinforced"),
            ("militarygrade", "Military Grade"),
            ("mirrored", "Mirrored"),
            ("reactive", "Reactive"),
            ("heavyduty", "Heavy Duty"),
            ("blast", "Blast Resistant"),
            ("kinetic", "Kinetic Resistant"),
            ("thermal", "Thermal Resistant"),
        ]
        for kw, label in keywords:
            if kw in lowered:
                return label

        # size + class/grade from Item e.g. int_bulkheads_size1_class1 → 1E, lakonminer_armour_grade1 → 1E
        size_m = re.search(r"_?size(\d+)", lowered)
        grade_m = re.search(r"_?(?:class|grade)(\d+)", lowered)
        if grade_m:
            rating = _CLASS_TO_RATING.get(grade_m.group(1))
            size = size_m.group(1) if size_m else "1"  # bulkheads are always size 1
            if rating:
                return f"{size}{rating}"
            return None

        return None

    # size + class/grade from Item e.g. int_shieldgenerator_size5_class2 → 5D
    size_m = re.search(r"_size(\d+)", item)
    class_m = re.search(r"_(?:class|grade)(\d+)", item)
    if size_m and class_m:
        rating = _CLASS_TO_RATING.get(class_m.group(1))
        if rating:
            return f"{size_m.group(1)}{rating}"

    # fallback: try to extract from localised name e.g. "Shield Generator 5D"
    localised = m.get("Module_Localised") or m.get("Item_Localised") or ""
    if localised:
        m2 = re.search(r"\b(\d+)([A-E])\b", localised)
        if m2:
            return f"{m2.group(1)}{m2.group(2)}"

    return None


def _module_name(m: dict) -> str:
    localised = m.get("Module_Localised") or m.get("Item_Localised") or ""
    if localised:
        return localised
    slot = m.get("Slot", "")
    if slot in _SLOT_NAMES:
        return _SLOT_NAMES[slot]
    item = m.get("Item", "")
    if item:
        return _clean_item_name(item)
    return slot or "?"


def _slot_category(slot: str) -> str:
    if slot.startswith(HARDPOINT_PREFIXES):
        return "hardpoints"
    if slot.startswith(UTILITY_PREFIX):
        return "utility"
    if slot in CORE_SLOTS:
        return "core"
    if slot.startswith(OPTIONAL_PREFIXES) or slot == "PlanetaryApproachSuite":
        return "optional"
    return "other"


def _slot_sort_key(slot: str) -> tuple:
    cat_order = {"hardpoints": 0, "utility": 1, "core": 2, "optional": 3, "other": 4}
    cat = _slot_category(slot)
    return (cat_order.get(cat, 9), slot)


def read_journal_dir(config_path: str | None = None) -> str | None:
    return find_journal_dir(config_path)


def find_last_loadout(journal_file: str) -> dict | None:
    if not journal_file or not os.path.exists(journal_file):
        return None
    result = None
    with open(journal_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("event") == "Loadout":
                result = ev
    return result


def read_status(journal_dir: str) -> dict | None:
    path = os.path.join(journal_dir, "Status.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _ship_name(loadout: dict) -> str:
    localised = loadout.get("Ship_Localised") or ""
    if localised:
        return localised
    raw = loadout.get("Ship", "")
    if raw in _KNOWN_SHIPS:
        return _KNOWN_SHIPS[raw]
    if raw:
        return raw.replace("_", " ").title()
    return ""


def find_last_cargo(journal_dir: str) -> list | None:
    files = sorted(glob.glob(os.path.join(journal_dir, "Journal.*.log")), reverse=True)
    total = len(files)
    result = None
    for i, jf in enumerate(files, 1):
        print_progress(i, total, suffix="files (cargo)")
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("event") == "Cargo":
                    inv = ev.get("Inventory")
                    if inv:
                        result = inv
    return result


def find_current_economy(journal_dir: str) -> str | None:
    files = sorted(glob.glob(os.path.join(journal_dir, "Journal.*.log")), reverse=True)
    total = len(files)
    for i, jf in enumerate(files, 1):
        print_progress(i, total, suffix="files (economy)")
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = ev.get("event", "")
                if event in ("Location", "FSDJump"):
                    economy = ev.get("SystemEconomy_Localised") or ev.get("SystemEconomy", "")
                    if economy:
                        print_progress(total, total, suffix="files (economy)")
                        return economy
    print_progress(total, total, suffix="files (economy)")
    return None


def _read_cargo_json(journal_dir: str) -> list | None:
    path = os.path.join(journal_dir, "Cargo.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("Inventory")
    except (json.JSONDecodeError, OSError):
        return None


def get_ship_data(journal_dir: str) -> dict:
    result = {
        "ship": "",
        "hull_health": None,
        "shield_health": None,
        "shield_gen": False,
        "shield_gen_health": None,
        "cargo_capacity": 0,
        "cargo_current": 0,
        "cargo_items": [],
        "cargo_value": None,
        "modules": [],
        "ship_value": None,
        "rebuy": None,
        "credits": None,
        "economy": None,
    }
    jfile = get_latest_journal(journal_dir)
    loadout = find_last_loadout(jfile) if jfile else None
    if loadout:
        result["ship"] = _ship_name(loadout)
        result["hull_health"] = loadout.get("HullHealth")
        result["ship_value"] = (loadout.get("HullValue") or 0) + (loadout.get("ModulesValue") or 0)
        result["rebuy"] = loadout.get("Rebuy")
        result["cargo_capacity"] = loadout.get("CargoCapacity", 0)
        result["cargo_current"] = loadout.get("Cargo", 0)
        modules = loadout.get("Modules", [])
        for m in modules:
            slot = m.get("Slot", "")
            if slot in ("VesselVoice", "ShipCockpit") or slot.startswith("Decal"):
                continue
            item = m.get("Item", "")
            if "shieldgenerator" in item.lower():
                result["shield_gen"] = True
                result["shield_gen_health"] = m.get("Health", 1.0)
            result["modules"].append({
                "slot": slot,
                "name": _module_name(m),
                "rating": _module_rating(m),
                "health": m.get("Health", 1.0),
                "category": _slot_category(slot),
            })
        result["modules"].sort(key=lambda x: _slot_sort_key(x["slot"]))

    status = read_status(journal_dir)
    status_module_health: dict[str, float] = {}
    if status:
        if "ShieldHealth" in status:
            result["shield_health"] = status["ShieldHealth"]
        if "Cargo" in status:
            result["cargo_current"] = status["Cargo"]
        if "Balance" in status:
            result["credits"] = status["Balance"]
        for sm in status.get("Modules", []):
            slot = sm.get("Slot", "")
            health = sm.get("Health")
            if slot and health is not None:
                status_module_health[slot] = health

    result["economy"] = find_current_economy(journal_dir)

    # override module health from real-time Status.json
    for m in result["modules"]:
        if m["slot"] in status_module_health:
            m["health"] = status_module_health[m["slot"]]

    # cargo manifest from Cargo.json (updated in real-time) or fallback to journal
    cargo_manifest = _read_cargo_json(journal_dir) or find_last_cargo(journal_dir)
    if cargo_manifest:
        for i in cargo_manifest:
            count = i.get("Count", 0)
            if count:
                name = i.get("Name_Localised") or i.get("Name", "?")
                price = _COMMODITY_PRICES.get(name.lower())
                result["cargo_items"].append({
                    "name": name,
                    "count": count,
                    "price": price,
                    "stolen": i.get("Stolen", 0),
                })

    result["cargo_value"] = _cargo_total_value(result["cargo_items"])
    return result


def _cargo_total_value(items: list) -> int | None:
    total = 0
    for ci in items:
        price = ci.get("price")
        if price is None:
            continue
        if price > 0:
            total += price * ci["count"]
    return total


CATEGORY_LABELS = {
    "hardpoints": "Hardpoints",
    "utility": "Utility Mounts",
    "core": "Core Internal",
    "optional": "Optional Internal",
    "other": "Other",
}
