"""Shared event formatting for CLI and webui."""

import re
import sys


def print_progress(current: int, total: int, *, width: int = 20, suffix: str = ""):
    """Print an ASCII progress bar to stderr. Call with current==total to finalize."""
    if "uvicorn" in sys.modules:
        return
    pct = current / total if total else 1
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    sys.stderr.write(f"\r  {bar}  {current}/{total} {suffix}  ")
    sys.stderr.flush()
    if current == total:
        sys.stderr.write("\n")


def _parse_localisation_key(key: str) -> str:
    """Parse a $ delimited localization key into readable text."""
    if not key or not isinstance(key, str) or not key.startswith("$"):
        return key
    key = key.lstrip("$").rstrip(";")

    # $Codex_Ent_<Genus>_<Num>_<Species>_Name  → "Genus Species Type Num"
    m = re.match(r"Codex_Ent_([A-Za-z]+)_(\d+)_([A-Za-z]+)_Name$", key)
    if m:
        return f"{m.group(1)} {m.group(3)} Type {m.group(2)}"

    # Strip known Codex prefixes for cleaner output
    key = re.sub(r"^(?:Codex_Ent_|Codex_SubCategory_|Codex_Category_)", "", key)

    return key.replace("_", " ").strip()


def _cap(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def _resolve_field(data: dict, field: str, default: str = "") -> str:
    """Resolve a journal field: _Localised → raw → parse $ key."""
    val = data.get(f"{field}_Localised", data.get(field, default))
    if val and isinstance(val, str):
        if not val.startswith("$"):
            return val
        raw = data.get(field, default)
        if raw and isinstance(raw, str) and not raw.startswith("$"):
            return raw
        return _parse_localisation_key(val or raw)
    return val if val is not None else default


def fmt_tons(v: float) -> str:
    return f"{v:,.2f} T"


def fmt_cr(v: float | int) -> str:
    return f"{v:,.0f} Cr"


def fmt_mass(v: float) -> str:
    return f"{v:,.1f}"


UGT_YEAR_OFFSET = 1286


def fmt_date(ts: str) -> str:
    if "T" not in ts:
        return ts
    try:
        date_part = ts[:10]
        year = int(date_part[:4]) + UGT_YEAR_OFFSET
        return f"{year}-{date_part[5:]}"
    except (ValueError, IndexError):
        return ts[:10]


def fmt_time(ts: str) -> str:
    return (ts[11:19] if "T" in ts else ts) + " UGT"


def fmt_event(data: dict) -> str | None:
    """Brief formatting for the Flight Recorder / CLI."""
    return _fmt_event(data, narrative=False)


def fmt_captains_log(data: dict) -> str | None:
    """Narrative-style formatting for the Captain's Log."""
    return _fmt_event(data, narrative=True)


def _fmt_event(data: dict, narrative: bool = False) -> str | None:
    event = data.get("event", "")

    if event == "Fileheader":
        return None

    if event == "LoadGame":
        ship = data.get("Ship_Localised", data.get("Ship", ""))
        cmd = data.get("Commander", "")
        creds = fmt_cr(data.get("Credits", 0))
        if narrative:
            return f"Loaded into {ship} as {cmd}. Credits: {creds}"
        return f"Loaded: {ship} / {cmd} / {creds}"

    if event == "FSDJump":
        sys_name = data.get("StarSystem", "")
        dist = data.get("JumpDist", 0)
        fuel = data.get("FuelUsed", 0)
        body = data.get("Body", "")
        if narrative:
            out = f"Jumped to {sys_name}"
            parts = []
            if body:
                parts.append(f"arrived at {body}")
            if dist:
                parts.append(f"{fmt_mass(dist)} ly jump")
            if fuel:
                parts.append(f"used {fmt_tons(fuel)} fuel")
            if parts:
                out += " (" + "; ".join(parts) + ")"
            return out
        out = f"Jumped to {sys_name}"
        if dist:
            out += f"  ({fmt_tons(dist)})"
        if fuel:
            out += f"  fuel: {fmt_tons(fuel)}"
        return out

    if event == "StartJump":
        kind = data.get("JumpType", "Jump")
        sys_name = data.get("StarSystem", "")
        if not sys_name:
            return None if narrative else f"Initiated {kind}"
        if narrative:
            return f"Charging {kind} to {sys_name}"
        return f"Initiated {kind} to {sys_name}"

    if event == "SupercruiseEntry":
        if narrative:
            return f"Entered supercruise"
        return f"Supercruise entered  ({data.get('StarSystem', '')})"

    if event == "SupercruiseExit":
        sys_name = data.get("StarSystem", "")
        body = data.get("Body", "")
        if narrative:
            out = f"Dropped from supercruise at {sys_name}"
            if body:
                out += f" near {body}"
            return out
        return f"Supercruise exited  ({sys_name})"

    if event == "Docked":
        station = data.get("StationName", "")
        sys_name = data.get("StarSystem", "")
        s_type = data.get("StationType", "")
        pad = data.get("LandingPad", "")
        if narrative:
            out = f"Docked at {station}"
            if sys_name:
                out += f" in the {sys_name} system"
            parts = []
            if s_type:
                parts.append(s_type)
            if pad:
                parts.append(f"pad {pad}")
            if parts:
                out += " (" + "; ".join(parts) + ")"
            return out
        pad_str = f" pad{pad}" if pad else ""
        return f"Docked at {station}  ({sys_name})  [{s_type}{pad_str}]"

    if event == "Undocked":
        station = data.get("StationName", "")
        sys_name = data.get("StarSystem", "")
        if narrative:
            out = f"Departed from {station}"
            if sys_name:
                out += f" in the {sys_name} system"
            return out
        return f"Undocked from {station}"

    if event == "DockingGranted":
        station = data.get("StationName", "")
        pad = data.get("LandingPad", "")
        if narrative:
            out = f"Docking clearance granted at {station}"
            if pad:
                out += f" (pad {pad})"
            return out
        return f"Docking granted at {station}  pad {pad}"

    if event == "Touchdown":
        body = data.get("Body", "")
        sys_name = data.get("StarSystem", "")
        grav = data.get("Gravity", 0)
        if narrative:
            out = f"Landed on {body}"
            if sys_name:
                out += f" in the {sys_name} system"
            if grav:
                out += f" (gravity: {grav:.2f}g)"
            return out
        out = f"Landed on {body}"
        if grav:
            out += f"  (gravity: {grav:.2f}g)"
        return out

    if event == "Liftoff":
        body = data.get("Body", "")
        sys_name = data.get("StarSystem", "")
        if narrative:
            out = f"Liftoff from {body}"
            if sys_name:
                out += f" in the {sys_name} system"
            return out
        return f"Liftoff from {body}"

    if event == "ApproachBody":
        body = data.get("Body", "")
        sys_name = data.get("StarSystem", "")
        if narrative:
            out = f"Approaching {body}"
            if sys_name:
                out += f" in the {sys_name} system"
            return out
        return f"Approaching {body}"

    if event == "LeaveBody":
        return f"Left {data.get('Body', '')}"

    if event == "MaterialCollected":
        name = data.get("Name_Localised") or _cap(data.get("Name", ""))
        cnt = data.get("Count", 1)
        cat = data.get("Category", "")
        if narrative:
            out = f"Picked up {cnt}x {name}"
            if cat and cat not in ("Encoded", "Raw", "Manufactured"):
                out += f" ({cat})"
            return out
        return f"Collected {name} x{cnt}  ({cat})"

    if event == "MaterialDiscarded":
        name = data.get("Name_Localised") or _cap(data.get("Name", ""))
        cnt = data.get("Count", 1)
        if narrative:
            return f"Discarded {cnt}x {name}"
        return f"Discarded {name} x{cnt}"

    if event == "MaterialDiscovered":
        name = data.get("Name_Localised") or _cap(data.get("Name", ""))
        cat = data.get("Category", "")
        if narrative:
            out = f"Discovered {name}"
            if cat:
                out += f" ({cat} material)"
            return out
        return f"Discovered material: {name}  ({cat})"

    if event == "MaterialTrade":
        pay = _cap(data.get("Paid", {}).get("Material", ""))
        pay_q = data.get("Paid", {}).get("Quantity", 1)
        recv = _cap(data.get("Received", {}).get("Material", ""))
        recv_q = data.get("Received", {}).get("Quantity", 1)
        if narrative:
            return f"Traded {pay_q}x {pay} for {recv_q}x {recv}"
        return f"Traded {pay} x{pay_q} → {recv} x{recv_q}"

    if event == "MiningRefined":
        item = data.get("Type_Localised", data.get("Type", ""))
        cnt = data.get("Amount", 1)
        if narrative:
            return f"Refined {cnt}x {item} from mining"
        return f"Refined {item} x{cnt}"

    if event == "CollectCargo":
        if narrative:
            name = data.get("Name_Localised") or _cap(data.get("Name", data.get("Type", "")))
            cnt = data.get("Count", 1)
            cat = data.get("Category", "")
            out = f"Picked up {cnt}x {name}"
            if cat and cat not in ("Encoded", "Raw", "Manufactured"):
                out += f" ({cat})"
            return out
        return f"Collected cargo: {data.get('Type', '')}"

    if event == "MarketBuy":
        item = data.get("Type_Localised", data.get("Type", ""))
        qty = data.get("Count", 1)
        cost = fmt_cr(data.get("TotalCost", 0))
        return f"Bought {qty}x {item} for {cost}"

    if event == "MarketSell":
        item = data.get("Type_Localised", data.get("Type", ""))
        qty = data.get("Count", 1)
        gain = fmt_cr(data.get("TotalSale", 0))
        return f"Sold {qty}x {item} for {gain}"

    if event == "Bounty":
        target = data.get("Target", "")
        reward = fmt_cr(data.get("TotalReward", 0))
        if narrative:
            out = f"Claimed {reward} bounty"
            if target:
                out += f" for {target}"
            return out
        out = f"Bounty: {reward}"
        if target:
            out += f"  ({target})"
        return out

    if event == "Died":
        killer = data.get("KillerName", "")
        rebuy = fmt_cr(data.get("RebuyCost", 0))
        if narrative:
            out = f"Ship destroyed! Rebuy cost: {rebuy}"
            if killer:
                out += f" (killed by {killer})"
            return out
        out = f"Destroyed! Rebuy: {rebuy}"
        if killer:
            out += f"  (killed by {killer})"
        return out

    if event == "Resurrect":
        cost = fmt_cr(data.get("Cost", 0))
        if narrative:
            return f"Resurrected at {data.get('Station', 'the rebuy screen')} for {cost}"
        return f"Resurrected  cost: {cost}"

    if event == "RedeemVoucher":
        vtype = data.get("Type", "")
        amount = fmt_cr(data.get("Amount", 0))
        if narrative:
            return f"Redeemed {vtype} voucher for {amount}"
        return f"Redeemed {vtype} voucher: {amount}"

    if event == "MissionAccepted":
        name = data.get("Name_Localised", data.get("Name", ""))
        faction = data.get("Faction", "")
        reward = fmt_cr(data.get("Reward", 0)) if "Reward" in data else ""
        if narrative:
            out = f"Accepted mission: {name} ({faction})"
            if reward:
                out += f" — reward: {reward}"
            return out
        out = f"Accepted mission: {name}  ({faction})"
        if reward:
            out += f"  reward: {reward}"
        return out

    if event == "MissionCompleted":
        name = data.get("Name_Localised", data.get("Name", ""))
        faction = data.get("Faction", "")
        reward = fmt_cr(data.get("Reward", 0)) if "Reward" in data else ""
        if narrative:
            out = f"Completed mission: {name} ({faction})"
            if reward:
                out += f" — reward: {reward}"
            return out
        out = f"Completed mission: {name}  ({faction})"
        if reward:
            out += f"  reward: {reward}"
        return out

    if event == "EngineerCraft":
        eng = data.get("Engineer", "")
        mod = data.get("BlueprintName", "")
        lvl = data.get("BlueprintLevel", "")
        if narrative:
            out = f"Engineered by {eng}"
            if mod:
                out += f": {mod}"
            if lvl:
                out += f" (grade {lvl})"
            return out
        out = f"Engineered by {eng}"
        if mod:
            out += f"  {mod}"
        if lvl:
            out += f"  (level {lvl})"
        return out

    if event == "FuelScoop":
        scooped = fmt_tons(data.get("Scooped", 0))
        total = fmt_tons(data.get("Total", 0))
        if narrative:
            return f"Scooped {scooped} fuel from the star (total onboard: {total})"
        return f"Fuel scooped: {scooped}  (total: {total})"

    if event == "BuyAmmo":
        cost = fmt_cr(data.get("Cost", 0))
        if narrative:
            return f"Restocked ammunition for {cost}"
        return f"Bought ammo: {cost}"

    if event == "Repair":
        cost = fmt_cr(data.get("Cost", 0))
        if narrative:
            return f"Repairs completed: {cost}"
        return f"Repairs: {cost}"

    if event == "Refuel":
        cost = fmt_cr(data.get("Cost", 0))
        amt = fmt_tons(data.get("Amount", 0))
        if narrative:
            return f"Refueled {amt} for {cost}"
        return f"Refuel: {amt}  cost: {cost}"

    if event == "SellExplorationData":
        systems = ", ".join(data.get("Systems", []))
        value = fmt_cr(data.get("BaseValue", 0))
        bonus = fmt_cr(data.get("Bonus", 0)) if "Bonus" in data else ""
        if narrative:
            out = f"Sold exploration data for {value}"
            if bonus:
                out += f" (bonus: {bonus})"
            if systems:
                out += f" — systems: {systems}"
            return out
        out = f"Sold exploration data: {value}"
        if bonus:
            out += f"  bonus: {bonus}"
        if systems:
            out += f"  ({systems})"
        return out

    if event == "MultiSellExplorationData":
        value = fmt_cr(data.get("TotalEarnings", 0))
        disc = len(data.get("Discovered", []))
        mapped = len(data.get("Mapped", []))
        if narrative:
            out = f"Sold exploration data for {value}"
            parts = []
            if disc:
                parts.append(f"{disc} discovered")
            if mapped:
                parts.append(f"{mapped} mapped")
            if parts:
                out += f" ({'; '.join(parts)})"
            return out
        return f"Sold exploration data: {value}  ({disc} bodies)"

    if event == "BuyExplorationData":
        sys_name = data.get("System", "")
        cost = fmt_cr(data.get("Cost", 0))
        if narrative:
            return f"Purchased exploration data for {sys_name} ({cost})"
        return f"Bought exploration data: {sys_name}  ({cost})"

    if event == "Scan":
        body = data.get("BodyName", "")
        btype = data.get("StarType", data.get("PlanetClass", ""))
        dist = data.get("DistanceFromArrivalLS", 0)
        if narrative:
            out = f"Scanned {body}"
            if btype:
                out += f" — {btype}"
            if dist:
                out += f" ({fmt_mass(dist)} ls from arrival)"
            return out
        out = f"Scanned {body}"
        if btype:
            out += f"  [{btype}]"
        if dist:
            out += f"  {dist:,.2f} ls"
        return out

    if event == "SAAScanComplete":
        body = data.get("BodyName", "")
        probes = data.get("ProbesUsed", 0)
        if narrative:
            mappings = data.get("MappingsComplete")
            out = f"Completed surface scan of {body} ({probes} probes)"
            if mappings:
                out += f" — {mappings} mappings"
            return out
        return f"Surface scan: {body}  ({probes} probes)"

    if event == "CodexEntry":
        name = _resolve_field(data, "Name", "")
        cat = _resolve_field(data, "Category", "")
        sys_name = data.get("System", "")
        if narrative:
            subcat = _resolve_field(data, "SubCategory", "")
            out = f"Logged Codex entry: {name}"
            if subcat:
                out += f" ({subcat})"
            if cat:
                out += f" — {cat}"
            if sys_name:
                out += f" in the {sys_name} system"
            return out
        out = f"Codex entry: {name}"
        if cat:
            out += f"  [{cat}]"
        if sys_name:
            out += f"  in {sys_name}"
        return out

    if event == "EjectCargo":
        ctype = data.get("Type", "")
        cnt = data.get("Count", 1)
        if narrative:
            return f"Jettisoned {cnt}x {ctype}"
        return f"Jettisoned cargo: {ctype} x{cnt}"

    if event == "LaunchDrone":
        if narrative:
            return None
        dt = data.get("Type", "")
        dmap = {"Collection": "Collector Limpet", "Prospector": "Prospector Limpet",
                "Repair": "Repair Limpet", "FuelTransfer": "Fuel Limpet",
                "HatchBreaker": "Hatch Breaker Limpet"}
        return f"Launched: {dmap.get(dt, dt + ' Limpet' if dt else 'Limpet')}"

    if event == "CrewMemberJoins":
        crew = data.get("Crew", "")
        if narrative:
            return f"{crew or 'A crew member'} joined the crew"
        return f"Crew joined: {crew}"

    if event == "CrewMemberRoleChange":
        crew = data.get("Crew", "")
        role = data.get("Role", "")
        if narrative:
            return f"{crew or 'A crew member'} assigned to {role or 'a new role'}"
        return f"Crew {crew} → {role}"

    if event == "CrewMemberQuits":
        crew = data.get("Crew", "")
        if narrative:
            return f"{crew or 'A crew member'} left the crew"
        return f"Crew left: {crew}"

    if event == "BuyTradeData":
        sys_name = data.get("System", "")
        cost = fmt_cr(data.get("Cost", 0))
        if narrative:
            return f"Purchased trade data for {sys_name} ({cost})"
        return f"Bought trade data: {sys_name}  ({cost})"

    if event == "SetUserShipName":
        ship = data.get("Ship", "")
        name = data.get("UserShipName", "")
        if narrative:
            sid = data.get("UserShipId", "")
            out = f"Renamed {ship}"
            if name:
                out += f' to "{name}"'
            if sid:
                out += f" (ID: {sid})"
            return out
        return f"Renamed {ship} → {name}"

    if event == "ModuleBuy":
        cost = fmt_cr(data.get("BuyPrice", 0))
        if narrative:
            module = data.get("BuyItem_Localised", data.get("BuyItem", data.get("SellItem_Localised", data.get("SellItem", ""))))
            if not module:
                return None
            return f"Installed {module} for {cost}"
        module = data.get("SellItem_Localised", data.get("SellItem", ""))
        return f"Bought module: {module}  ({cost})"

    if event == "ModuleSell":
        module = data.get("SellItem_Localised", data.get("SellItem", ""))
        gain = fmt_cr(data.get("SellPrice", 0))
        if narrative:
            return f"Removed {module} — gained {gain}"
        return f"Sold module: {module}  ({gain})"

    if event == "ModuleStore":
        module = data.get("StoredItem_Localised", data.get("StoredItem", ""))
        if narrative:
            return f"Stored {module} in the shipyard"
        return f"Stored module: {module}"

    if event == "VehicleSwitch":
        return f"Switched to {data.get('To', '')}"

    if event == "FSSSignalDiscovered":
        if narrative:
            return None
        signal = data.get("SignalName_Localised") or data.get("SignalName", "")
        sys_name = data.get("StarSystem", "")
        out = f"Detected signal: {signal}"
        if sys_name:
            out += f" in {sys_name}"
        return out

    # --- Captain's Log only events ---
    if not narrative:
        return None

    if event == "BuyDrones":
        count = data.get("Count", 1)
        cost = fmt_cr(data.get("TotalCost", 0))
        return f"Bought {count} drones for {cost}"

    if event == "LaunchFighter":
        return f"Launched fighter"

    if event == "FighterRebuilt":
        return f"Rebuilt fighter"

    if event == "DockFighter":
        return f"Recalled fighter to bay"

    if event == "Powerplant":
        return f"Power plant status: {data.get('Status', 'unknown')}"

    if event == "BuySuit":
        suit = data.get("Name_Localised", data.get("Name", ""))
        cost = fmt_cr(data.get("Price", 0))
        return f"Purchased {suit} for {cost}"

    if event == "UpgradeSuit":
        suit = data.get("Name_Localised", data.get("Name", ""))
        cost = fmt_cr(data.get("Cost", 0))
        return f"Upgraded {suit} for {cost}"

    if event == "SellSuit":
        suit = data.get("Name_Localised", data.get("Name", ""))
        gain = fmt_cr(data.get("Price", 0))
        return f"Sold {suit} for {gain}"

    if event == "BackpackChange":
        items = data.get("Items", [])
        out_parts = []
        for item in items:
            name = item.get("Name_Localised", item.get("Name", ""))
            cnt = item.get("Count", 1)
            if name:
                out_parts.append(f"{cnt}x {name}")
        if out_parts:
            return f"Backpack contents: {', '.join(out_parts)}"
        return None

    if event == "CollectItems":
        items = data.get("Items", [])
        out_parts = []
        biome = data.get("Biome", "")
        for item in items:
            name = item.get("Name_Localised", item.get("Name", ""))
            cnt = item.get("Count", 1)
            if name:
                out_parts.append(f"{cnt}x {name}")
        if out_parts:
            out = f"Collected: {', '.join(out_parts)}"
            if biome:
                out += f" ({biome})"
            return out
        return None

    if event == "UseConsumable":
        item = data.get("Name_Localised", data.get("Name", ""))
        return f"Used {item}"

    if event == "CreateSuitLoadout":
        name = data.get("LoadoutName", "")
        suit = data.get("SuitName_Localised", data.get("SuitName", ""))
        out = "Created loadout"
        if name:
            out += f' "{name}"'
        if suit:
            out += f" for {suit}"
        return out

    if event == "DeleteSuitLoadout":
        name = data.get("LoadoutName", "")
        return f'Deleted loadout "{name}"' if name else "Deleted a suit loadout"

    if event == "SwitchSuitLoadout":
        name = data.get("LoadoutName", "")
        suit = data.get("SuitName_Localised", data.get("SuitName", ""))
        out = "Switched to loadout"
        if name:
            out += f' "{name}"'
        if suit:
            out += f" ({suit})"
        return out

    if event == "ShipLocker":
        return None

    if event == "ReceiveText":
        from_ = data.get("From", "")
        msg = data.get("Message_Localised", data.get("Message", ""))
        if not msg or msg.startswith("Entered Channel"):
            return None
        if from_ and from_.startswith("$npc_name_decorate"):
            parts = from_.split("#name=")
            if len(parts) > 1:
                from_ = parts[1].rstrip(";")
        out = f'Message from {from_}: "{msg}"' if from_ else f'Message: "{msg}"'
        return out

    if event == "FSSAllBodiesFound":
        count = data.get("Count", 0)
        sys_name = data.get("SystemName", "")
        out = f"Full system scan complete: {count} bodies"
        if sys_name:
            out += f" in {sys_name}"
        return out

    if event == "DiscoveryScan":
        bodies = data.get("NumBodies", 0)
        sys_name = data.get("SystemName", "")
        out = f"Discovery scan: {bodies} bodies found"
        if sys_name:
            out += f" in {sys_name}"
        return out

    if event == "NavBeaconScan":
        bodies = data.get("NumBodies", 0)
        sys_name = data.get("SystemName", "")
        out = f"Downloaded nav beacon data: {bodies} bodies"
        if sys_name:
            out += f" in {sys_name}"
        return out

    if event == "ScanOrganic":
        species = data.get("Species_Localised", data.get("Species", ""))
        genus = data.get("Genus_Localised", data.get("Genus", ""))
        body = data.get("Body", "")
        out = f"Scanned organic life: {species}"
        if genus:
            out += f" (genus: {genus})"
        if body:
            out += f" on {body}"
        return out

    if event == "SellOrganicData":
        items = data.get("BioData", [])
        total = fmt_cr(data.get("TotalValue", 0))
        parts = []
        for item in items:
            name = item.get("Species_Localised", item.get("Species", ""))
            if name:
                s = name
                if item.get("Bonus"):
                    s += " (first discovery bonus!)"
                parts.append(s)
        out = f"Sold organic data for {total}"
        if parts:
            out += " — " + ", ".join(parts)
        return out

    if event == "BuyOrganicData":
        cost = fmt_cr(data.get("Price", 0))
        return f"Purchased organic data for {cost}"

    if event == "ReservoirReplenished":
        materials = data.get("FuelReservoir", {})
        if isinstance(materials, dict):
            main = materials.get("Main", materials)
            reserve = materials.get("Reserve", 0)
            out = f"Fuel replenished: {fmt_tons(main)} main"
            if reserve:
                out += f", {fmt_tons(reserve)} reserve"
            return out
        return None

    if event == "CarrierJump":
        sys_name = data.get("StarSystem", "")
        body = data.get("Body", "")
        out = f"Fleet carrier jumped to {sys_name}"
        if body:
            out += f" near {body}"
        return out

    if event == "CarrierBuy":
        name = data.get("CallingName", "")
        cost = fmt_cr(data.get("Price", 0))
        out = 'Purchased fleet carrier'
        if name:
            out += f' "{name}"'
        if data.get("Price"):
            out += f" for {cost}"
        return out

    if event == "CarrierFinance":
        tax = data.get("TaxRate", 0)
        reserve = data.get("ReserveBalance", 0)
        out = f"Fleet carrier finances — tax: {tax}%"
        if reserve:
            out += f", reserve: {fmt_cr(reserve)}"
        return out

    if event == "CarrierStatistics":
        return None

    if event in ("CarrierShipPack", "CarrierModulePack"):
        pack = data.get("PackTheme", "")
        cost = fmt_cr(data.get("Cost", 0))
        return f"Purchased {pack} for carrier for {cost}"

    if event == "Location":
        sys_name = data.get("StarSystem", "")
        body = data.get("Body", "")
        station = data.get("StationName", "")
        out = f"Located in the {sys_name} system"
        if body:
            out += f" at {body}"
        if station:
            out += f" (docked at {station})"
        return out

    if event == "SocietalProxy":
        proxy = data.get("Title", "")
        cost = fmt_cr(data.get("Cost", 0)) if "Cost" in data else ""
        out = f"Societal proxy: {proxy}"
        if cost:
            out += f" — cost: {cost}"
        return out

    if event == "ShipTargeted":
        target = data.get("PilotName_Localised", data.get("PilotName", ""))
        ship = data.get("Ship_Localised", data.get("Ship", ""))
        out = "Targeting"
        if ship:
            out += f" {ship}"
        if target:
            out += f" — {target}"
        return out

    if event == "CommitCrime":
        crime = data.get("CrimeType", "")
        fine = fmt_cr(data.get("Fine", 0)) if "Fine" in data else ""
        victim = data.get("Victim", "")
        out = f"Commited: {crime}"
        if fine:
            out += f" — fine: {fine}"
        if victim:
            out += f" (victim: {victim})"
        return out

    if event == "PayFines":
        amount = fmt_cr(data.get("Amount", 0))
        return f"Paid fines: {amount}"

    if event == "Promotion":
        rank = data.get("Rank", "")
        out = "Promoted!"
        if rank:
            out += f" — {rank}"
        return out

    return None
