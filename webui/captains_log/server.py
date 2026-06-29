import json
import os
import sys
from collections import defaultdict

from fastapi import FastAPI, Query as Q
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from blackbox.formatter import fmt_date, fmt_time, fmt_captains_log
from webui._utils import resolve_db, get_conn

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

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
    "Location": "nav",
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

    if event in ("SocialProject",):
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
        raw = data.get("Name", "")
        if raw.startswith("$"):
            name = raw
        else:
            try:
                name = json.loads(raw).get("EN", raw) if raw.startswith("{") else raw
            except Exception:
                name = raw
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
        rows = conn.execute(
            "SELECT timestamp, event, raw_json FROM events ORDER BY timestamp"
        ).fetchall()
        if not rows:
            return {
                "ok": True, "days": [], "all_dates": [], "ships": [],
            }

        # --- Pass 1: compute sessions, ships, per-day financials from ALL events ---
        current_ship = "Unknown"
        session_id = -1
        all_ships: set[str] = set()
        all_dates: set[str] = set()
        sessions: dict[int, dict] = {}
        _session: dict | None = None

        per_day_financial: dict[str, dict] = defaultdict(
            lambda: {"income": 0, "expenses": 0}
        )

        for ts, event, raw in rows:
            data = json.loads(raw)
            d = fmt_date(ts)
            all_dates.add(d)

            # implicit session before first LoadGame
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
                current_ship = data.get("Ship_Localised", data.get("Ship", "Unknown"))
                all_ships.add(current_ship)
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

                cr_chg, _ = _get_credits_change(event, data)
                if cr_chg > 0:
                    _session["credits_earned"] += cr_chg
                elif cr_chg < 0:
                    _session["credits_spent"] += abs(cr_chg)

            cr_chg, _ = _get_credits_change(event, data)
            if cr_chg > 0:
                per_day_financial[d]["income"] += cr_chg
            elif cr_chg < 0:
                per_day_financial[d]["expenses"] += abs(cr_chg)

        # build serializable sessions map
        serialized_sessions: dict[str, dict] = {}
        for sid, s in sessions.items():
            serialized_sessions[str(sid)] = {
                "ship": s["ship"],
                "jumps": s["jumps"],
                "bounties": s["bounties"],
                "missions": s["missions"],
                "scans": s["scans"],
                "organic_scans": s["organic_scans"],
                "landings": s["landings"],
                "docks": s["docks"],
                "systems_count": len(s["systems_visited"]),
                "events_count": s["events_count"],
                "credits_earned": s["credits_earned"],
                "credits_spent": s["credits_spent"],
            }

        # --- Pass 2: build response (apply date filter) ---
        current_ship = "Unknown"
        session_id = -1
        days: dict[str, dict] = {}

        for ts, event, raw in rows:
            data = json.loads(raw)
            d = fmt_date(ts)

            if date and d != date:
                continue

            # re-track ship/session for the event
            if event == "LoadGame":
                current_ship = data.get("Ship_Localised", data.get("Ship", "Unknown"))
                session_id += 1
            elif session_id == -1:
                session_id = 0
                current_ship = "Unknown"

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
                "credits_change": _get_credits_change(event, data)[0] or 0,
                "is_first_discovery": _is_first_discovery(event, data),
                "is_milestone": is_milestone,
                "milestone_label": milestone_label,
                "category": CATEGORY.get(event, "other"),
            }

            if d not in days:
                days[d] = {"date": d, "events": [], "sessions": serialized_sessions}

            days[d]["events"].append(evt)

        # attach per-day financial data
        for d in days:
            fin = per_day_financial.get(d, {"income": 0, "expenses": 0})
            days[d]["financial"] = {
                "income": fin["income"],
                "expenses": fin["expenses"],
                "net": fin["income"] - fin["expenses"],
            }

        return {
            "ok": True,
            "days": [days[d] for d in sorted(days, reverse=True)],
            "all_dates": sorted(all_dates, reverse=True),
            "ships": sorted(all_ships),
        }
    finally:
        conn.close()
