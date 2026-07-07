import json
import os
from collections import defaultdict

from fastapi import FastAPI, Query as Q
from fastapi.responses import HTMLResponse

from blackbox.formatter import fmt_date, fmt_time, fmt_captains_log, UGT_YEAR_OFFSET, _resolve_field
from webui._utils import resolve_db, get_conn

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

_NON_SHIP_VEHICLES = frozenset({
    "TestBuggy",       # SRV Scarab
    "Lander01",        # Nomad SLV
    "ExplorationSuit", # on foot
})

sub_app = FastAPI(title="SPECTR Captain's Log")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


CATEGORY = {
    "FSDJump": "nav", "StartJump": "nav", "SupercruiseEntry": "nav", "SupercruiseExit": "nav",
    "Docked": "nav", "Undocked": "nav", "DockingGranted": "nav",
    "Touchdown": "land", "Liftoff": "land", "ApproachBody": "land", "LeaveBody": "land",
    "Bounty": "combat", "Died": "combat", "Resurrect": "combat", "RedeemVoucher": "combat",
    "MarketBuy": "trade", "MarketSell": "trade", "BuyTradeData": "trade",
    "MaterialCollected": "mat", "MaterialDiscarded": "mat", "MaterialDiscovered": "mat",
    "MaterialTrade": "mat", "MiningRefined": "mat",
    "MissionAccepted": "mission", "MissionCompleted": "mission",
    "LoadGame": "ship", "ModuleBuy": "ship", "ModuleSell": "ship", "ModuleStore": "ship",
    "Repair": "ship", "Refuel": "ship", "BuyAmmo": "ship", "FuelScoop": "ship",
    "SetUserShipName": "ship", "VehicleSwitch": "ship",
    "Scan": "explore", "SAAScanComplete": "explore", "CodexEntry": "explore",
    "SellExplorationData": "explore", "MultiSellExplorationData": "explore",
    "BuyExplorationData": "explore",
    "CrewMemberJoins": "crew", "CrewMemberRoleChange": "crew", "CrewMemberQuits": "crew",
    "CollectCargo": "cargo", "EjectCargo": "cargo", "LaunchDrone": "cargo",
    "EngineerCraft": "engineer",
    "ReceiveText": "onfoot", "ScanOrganic": "onfoot", "SellOrganicData": "onfoot",
    "BuyOrganicData": "onfoot", "BackpackChange": "onfoot", "CollectItems": "onfoot",
    "UseConsumable": "onfoot", "BuySuit": "onfoot", "UpgradeSuit": "onfoot",
    "SellSuit": "onfoot", "SwitchSuitLoadout": "onfoot", "CreateSuitLoadout": "onfoot",
    "DeleteSuitLoadout": "onfoot", "ShipLocker": "onfoot",
    "CarrierJump": "nav", "CarrierBuy": "ship", "CarrierFinance": "ship",
    "Location": "nav", "SocietalProxy": "trade",
}


def _get_credits_change(event: str, data: dict) -> tuple[int, str | None]:
    v: int | float = 0

    if event == "Bounty":
        v = data.get("TotalReward", 0)
        return (int(v), "Bounty") if v else (0, None)

    if event == "RedeemVoucher":
        v = data.get("Amount", 0)
        return (int(v), data.get("Type", "Voucher")) if v else (0, None)

    if event == "MissionCompleted":
        v = data.get("Reward") or 0
        don = data.get("Donation") or 0
        total = v + don
        return (int(total), "Mission reward") if total else (0, None)

    if event == "MarketSell":
        v = data.get("TotalSale", 0)
        return (int(v), "Trade") if v else (0, None)

    if event in ("SellExplorationData", "MultiSellExplorationData"):
        v = data.get("TotalEarnings", data.get("BaseValue", 0))
        return (int(v), "Exploration data") if v else (0, None)

    if event == "SellOrganicData":
        v = data.get("TotalValue", 0)
        return (int(v), "Organic data") if v else (0, None)

    if event == "ModuleSell":
        v = data.get("SellPrice", 0)
        return (int(v), "Module sale") if v else (0, None)

    if event == "MarketBuy":
        v = data.get("TotalCost", 0)
        return (-int(v), "Purchase") if v else (0, None)

    if event == "Repair":
        v = data.get("Cost", 0)
        return (-int(v), "Repairs") if v else (0, None)

    if event == "Refuel":
        v = data.get("Cost", 0)
        return (-int(v), "Refuel") if v else (0, None)

    if event == "BuyAmmo":
        v = data.get("Cost", 0)
        return (-int(v), "Ammunition") if v else (0, None)

    if event == "ModuleBuy":
        v = data.get("BuyPrice", 0)
        return (-int(v), "Module purchase") if v else (0, None)

    if event == "BuyDrones":
        v = data.get("TotalCost", 0)
        return (-int(v), "Drones") if v else (0, None)

    if event == "Died":
        v = data.get("RebuyCost", 0)
        return (-int(v), "Rebuy") if v else (0, None)

    if event == "Resurrect":
        v = data.get("Cost", 0)
        return (-int(v), "Resurrection") if v else (0, None)

    if event in ("PayFines", "PayLegacyFines"):
        v = data.get("Amount", 0)
        return (-int(v), "Fines") if v else (0, None)

    if event in ("BuyTradeData",):
        v = data.get("Cost", 0)
        return (-int(v), "Trade data") if v else (0, None)

    if event in ("BuyExplorationData",):
        v = data.get("Cost", 0)
        return (-int(v), "Exploration data") if v else (0, None)

    if event in ("BuyOrganicData",):
        v = data.get("Price", 0)
        return (-int(v), "Organic data") if v else (0, None)

    if event in ("BuySuit",):
        v = data.get("Price", 0)
        return (-int(v), "Suit purchase") if v else (0, None)

    if event in ("UpgradeSuit",):
        v = data.get("Cost", 0)
        return (-int(v), "Suit upgrade") if v else (0, None)

    if event == "CarrierBuy":
        v = data.get("Price", 0)
        return (-int(v), "Carrier purchase") if v else (0, None)

    if event in ("CarrierShipPack", "CarrierModulePack"):
        v = data.get("Cost", 0)
        return (-int(v), "Carrier pack") if v else (0, None)

    if event in ("SocietalProxy", "SocialProject"):
        v = data.get("Cost", 0)
        return (-int(v), "Donation") if v else (0, None)

    return (0, None)


def _is_first_discovery(event: str, data: dict) -> bool:
    if event == "SellOrganicData":
        for item in data.get("BioData", []):
            if item.get("Bonus", 0) > 0:
                return True
    if event == "SellExplorationData":
        if data.get("Bonus", 0) > 0:
            return True
    if event == "MultiSellExplorationData":
        if data.get("Discovered", []):
            return True
    return False


def _is_milestone(event: str, data: dict) -> tuple:
    if event == "Promotion":
        rank = data.get("Rank", "")
        label = f"Promoted — {rank}" if rank else "Promoted"
        return (True, label)

    if event == "Died":
        return (True, "Ship destroyed!")

    if event == "CarrierBuy":
        name = data.get("CallingName", "Fleet Carrier")
        return (True, f"Purchased {name}")

    if event in ("SellOrganicData", "SellExplorationData", "MultiSellExplorationData"):
        if _is_first_discovery(event, data):
            return (True, "First discovery!")

    if event == "CodexEntry":
        name = _resolve_field(data, "Name", "")
        if data.get("IsNewEntry", False):
            return (True, f"New Codex entry" if not name else f"New Codex: {name}")

    if event == "Docked":
        sys_name = data.get("StarSystem", "")
        station = data.get("StationName", "")
        if station == "Jameson Memorial" or sys_name == "Shinrarta Dezhra":
            return (True, "Docked at Founders World")
        if sys_name == "Sagittarius A*":
            return (True, "Arrived at Sagittarius A*!")
        if sys_name == "Colonia":
            return (True, "Arrived at Colonia!")

    return (False, None)


@sub_app.get("/api/captains-log")
def api_captains_log(
    date: str = Q(None, description="Filter by date YYYY-MM-DD"),
    db: str = Q(None, description="DB path override"),
):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        # Lightweight query for all_dates (convert to UGT for frontend)
        raw_dates = sorted(set(
            r[0] for r in conn.execute(
                "SELECT DISTINCT substr(timestamp, 1, 10) FROM events"
            ).fetchall()
        ), reverse=True)
        all_dates = [
            f"{int(d[:4]) + UGT_YEAR_OFFSET}{d[4:]}" for d in raw_dates
        ]
        all_ships = sorted(set(
            (r[0] or r[1]) for r in conn.execute(
                "SELECT DISTINCT json_extract(raw_json, '$.Ship_Localised'), json_extract(raw_json, '$.Ship') FROM events WHERE event = 'LoadGame'"
            ).fetchall()
            if r[1] and not any(r[1].startswith(v) for v in _NON_SHIP_VEHICLES)
        ))

        if not date:
            return {
                "ok": True, "days": [], "all_dates": all_dates, "ships": all_ships,
            }

        # Convert UGT date from frontend back to real date for SQL
        if len(date) == 10 and date[4] == '-' and date[7] == '-':
            yr = int(date[:4]) - UGT_YEAR_OFFSET
            real_date = f"{yr:04d}{date[4:]}"
        else:
            real_date = date
        date_prefix = real_date + "%"
        rows = conn.execute(
            "SELECT timestamp, event, raw_json FROM events WHERE timestamp LIKE ? ORDER BY timestamp",
            (date_prefix,),
        ).fetchall()
        if not rows:
            return {
                "ok": True, "days": [], "all_dates": all_dates, "ships": all_ships,
            }

        # Single pass: parse, compute sessions, build day entries
        current_ship = "Unknown"
        session_id = -1
        sessions: dict[int, dict] = {}
        _session: dict | None = None
        per_day_financial: dict[str, dict] = defaultdict(
            lambda: {"income": 0, "expenses": 0}
        )
        days: dict[str, dict] = {}

        for row in rows:
            ts, event, raw = row
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            cc, _ = _get_credits_change(event, data)
            d = fmt_date(ts)

            # track session state
            if session_id == -1 and event != "LoadGame":
                session_id = 0
                _session = {
                    "id": session_id, "ship": current_ship, "jumps": 0,
                    "bounties": 0, "missions": 0, "scans": 0, "organic_scans": 0,
                    "landings": 0, "docks": 0, "systems_visited": set(),
                    "events_count": 0, "credits_earned": 0, "credits_spent": 0,
                }
                sessions[session_id] = _session

            if event == "LoadGame":
                raw_id = data.get("Ship", "")
                if not any(raw_id.startswith(v) for v in _NON_SHIP_VEHICLES):
                    current_ship = data.get("Ship_Localised", raw_id)
                session_id += 1
                _session = {
                    "id": session_id, "ship": current_ship, "jumps": 0,
                    "bounties": 0, "missions": 0, "scans": 0, "organic_scans": 0,
                    "landings": 0, "docks": 0, "systems_visited": set(),
                    "events_count": 0, "credits_earned": 0, "credits_spent": 0,
                }
                sessions[session_id] = _session

            if _session is not None:
                _session["events_count"] += 1
                if event == "FSDJump":
                    _session["jumps"] += 1
                    sys_name = data.get("StarSystem", "")
                    if sys_name:
                        _session["systems_visited"].add(sys_name)
                elif event == "Bounty":
                    _session["bounties"] += 1
                elif event == "MissionCompleted":
                    _session["missions"] += 1
                elif event == "Scan":
                    _session["scans"] += 1
                elif event == "ScanOrganic":
                    _session["organic_scans"] += 1
                elif event == "Touchdown":
                    _session["landings"] += 1
                elif event == "Docked":
                    _session["docks"] += 1
                if cc > 0:
                    _session["credits_earned"] += cc
                elif cc < 0:
                    _session["credits_spent"] += abs(cc)

            if cc > 0:
                per_day_financial[d]["income"] += cc
            elif cc < 0:
                per_day_financial[d]["expenses"] += abs(cc)

            # build day event entry
            formatted = fmt_captains_log(data)
            if formatted is None:
                continue

            is_milestone, milestone_label = _is_milestone(event, data)

            evt = {
                "time": fmt_time(ts),
                "event": event,
                "formatted": formatted,
                "ship": current_ship,
                "session_id": session_id,
                "credits_change": cc or 0,
                "is_first_discovery": _is_first_discovery(event, data),
                "is_milestone": is_milestone,
                "milestone_label": milestone_label,
                "category": CATEGORY.get(event, "other"),
            }

            if d not in days:
                days[d] = {"date": d, "events": []}

            days[d]["events"].append(evt)

        # serialize sessions
        serialized_sessions: dict[str, dict] = {}
        for sid, s in sessions.items():
            serialized_sessions[str(sid)] = {
                "ship": s["ship"], "jumps": s["jumps"], "bounties": s["bounties"],
                "missions": s["missions"], "scans": s["scans"],
                "organic_scans": s["organic_scans"], "landings": s["landings"],
                "docks": s["docks"], "systems_count": len(s["systems_visited"]),
                "events_count": s["events_count"],
                "credits_earned": s["credits_earned"],
                "credits_spent": s["credits_spent"],
            }

        for d in days:
            days[d]["events"].reverse()
            days[d]["sessions"] = serialized_sessions
            fin = per_day_financial.get(d, {"income": 0, "expenses": 0})
            days[d]["financial"] = {
                "income": fin["income"],
                "expenses": fin["expenses"],
                "net": fin["income"] - fin["expenses"],
            }

        return {
            "ok": True,
            "days": [days[d] for d in sorted(days, reverse=True)],
            "all_dates": all_dates,
            "ships": all_ships,
        }
    finally:
        conn.close()
