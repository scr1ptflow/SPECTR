"""Jump Tracker — Route progress and jump history."""

import tkinter as tk
import tkinter.filedialog, tkinter.messagebox
import json
import os
import glob
import logging
from core.plugin_api import plugin, on, post_load
from core.journal import _resolve_journal_path

logger = logging.getLogger(__name__)

SCOOPABLE = {"O", "B", "A", "F", "G", "K", "M"}


@plugin(
    name="Jump Tracker",
    version="1.3.0",
    description="Route progress and jump history",
    position="center",
    width=350,
    height=180,
    journal_events=["FSDJump", "Location", "NavRoute", "NavRouteClear", "StartJump"],
    status_events=True,
    dynamic=False,
    settings_tab="Jump Tracker",
)
class JumpTracker:

    def create(self, ctx):
        self._jumps = 0
        self._total_dist = 0.0
        self._route = []
        self._current = ""
        self._journal_dir = ""
        self._navroute_mtime = 0
        self._poll_id = None
        self._fuel_main = 0.0
        self._fuel_capacity = 0.0
        self._custom_route = []
        self._custom_route_path = ""
        self._ctx = ctx
        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self._data_dir, exist_ok=True)
        self._load_state()

        self._lbl_system = ctx.add_label(text="System: —", anchor=tk.W, fg=ctx.accent)
        self._lbl_left = ctx.add_label(text="", anchor=tk.W)
        self._bottom_frame = tk.Frame(ctx.parent, bg=ctx.bg)
        self._bottom_frame.pack(fill=tk.X)
        self._lbl_route_dist = tk.Label(self._bottom_frame, text="", anchor=tk.W,
                                        bg=ctx.bg, fg=ctx.fg, font=ctx.font)
        self._lbl_route_dist.pack(side=tk.LEFT)
        self._lbl_next = tk.Label(self._bottom_frame, text="", anchor=tk.E,
                                  bg=ctx.bg, fg="#888888", font=ctx.font)
        self._lbl_neutrons = tk.Label(self._bottom_frame, text="", anchor=tk.E,
                                      bg=ctx.bg, fg="#4488ff", font=ctx.font)
        self._lbl_neutrons.pack(side=tk.RIGHT)
        self._lbl_next.pack(side=tk.RIGHT)

    def _stats_path(self):
        return os.path.join(self._data_dir, "stats.json")

    def _load_state(self):
        path = self._stats_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    state = json.load(f)
                self._jumps = state.get("jumps", 0)
                self._total_dist = state.get("distance_ly", 0.0)
            except (OSError, json.JSONDecodeError):
                pass

    def _save_state(self):
        path = self._stats_path()
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"jumps": self._jumps, "distance_ly": self._total_dist}, f)
            os.replace(tmp, path)
        except OSError as e:
            logger.warning(f"Failed to save jump stats: {e}")

    def _find_latest_journal(self):
        if not os.path.isdir(self._journal_dir):
            return None
        pattern = os.path.join(self._journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        return files[-1] if files else None

    def _recover_current_system(self):
        path = self._find_latest_journal()
        if not path:
            return
        try:
            size = os.path.getsize(path)
            chunk_size = min(size, 16384)
            with open(path, "rb") as f:
                f.seek(size - chunk_size)
                chunk = f.read(chunk_size)
            lines = chunk.decode("utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ev = data.get("event", "")
                    if ev in ("FSDJump", "Location"):
                        sys_name = data.get("StarSystem", "")
                        if sys_name:
                            self._current = sys_name
                            return
                except json.JSONDecodeError:
                    continue
        except (OSError, json.JSONDecodeError):
            pass

    # ── Custom route loading ──────────────────────────────────────────

    def _parse_json_route(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "result" in data:
            items = data["result"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        entries = []
        for item in items:
            if not isinstance(item, dict):
                continue
            sysname = (item.get("name") or item.get("system") or item.get("System Name") or "").strip()
            if not sysname:
                continue
            jumps = item.get("jumps", 0)
            neutron = item.get("neutron", False)
            if isinstance(neutron, str):
                neutron = neutron.strip().lower() == "yes"
            scoopable = item.get("scoopable", False)
            if isinstance(scoopable, str):
                scoopable = scoopable.strip().lower() == "yes"
            star_class = "N" if neutron else ("K" if scoopable else "")
            entries.append({
                "name": sysname,
                "star_class": star_class,
                "jumps": jumps,
            })
        return entries

    def _custom_route_path_file(self):
        return os.path.join(self._data_dir, "custom_route_path.json")

    def _save_custom_route_path(self):
        path = self._custom_route_path_file()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"path": self._custom_route_path}, f)
        except OSError as e:
            logger.warning(f"Failed to save custom route path: {e}")

    def _delete_custom_route_path(self):
        path = self._custom_route_path_file()
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:
            logger.warning(f"Failed to delete custom route path: {e}")

    def _load_custom_route(self, path, silent=False, save=True):
        try:
            if path.lower().endswith(".json"):
                route = self._parse_json_route(path)
            else:
                if not silent:
                    tk.messagebox.showwarning("Unsupported", "Only JSON files are supported.")
                return False
        except Exception as e:
            if not silent:
                tk.messagebox.showerror("Error", f"Failed to parse route file:\n{e}")
            return False

        if not route:
            if not silent:
                tk.messagebox.showwarning("Empty Route", "No systems found in the file.")
            return False

        self._custom_route = route
        self._custom_route_path = path
        self._update_route_text()
        self._refresh_path_label()
        if save:
            self._save_custom_route_path()
        return True

    def _restore_custom_route(self):
        path_file = self._custom_route_path_file()
        if not os.path.exists(path_file):
            return
        try:
            with open(path_file, encoding="utf-8") as f:
                data = json.load(f)
            saved_path = data.get("path", "")
            if saved_path and os.path.exists(saved_path):
                self._load_custom_route(saved_path, silent=True, save=False)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to restore custom route: {e}")

    def _clear_custom_route(self):
        self._custom_route = []
        self._custom_route_path = ""
        self._delete_custom_route_path()
        self._update_route_text()
        self._refresh_path_label()

    def _pick_route_file(self):
        parent = getattr(self, "_settings_parent", None)
        path = tk.filedialog.askopenfilename(
            title="Select Spansh Route File",
            filetypes=[("JSON files", "*.json")],
            parent=parent,
        )
        if path:
            self._load_custom_route(path)

    # ── NavRoute JSON ─────────────────────────────────────────────────

    def _read_navroute_json(self):
        path = os.path.join(self._journal_dir, "NavRoute.json")
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return
        if mtime <= self._navroute_mtime:
            return
        self._navroute_mtime = mtime
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        route_raw = data.get("Route") if isinstance(data, dict) else None
        if not route_raw:
            self._route = []
            self._update_route_text()
            return
        self._route = [{
            "name": entry.get("StarSystem", ""),
            "star_class": entry.get("StarClass", ""),
            "pos": entry.get("StarPos"),
        } for entry in route_raw if entry.get("StarSystem")]
        self._update_route_text()

    def _poll_navroute(self):
        if self._poll_id is None:
            return
        try:
            self._read_navroute_json()
            self._update_display()
            self._ctx.schedule(2000, self._poll_navroute)
        except tk.TclError:
            self._poll_id = None

    # ── Event handlers ────────────────────────────────────────────────

    @on("status")
    def on_status(self, ctx, data):
        try:
            fuel = ctx.status.fuel_main
            cap = ctx.status.fuel_capacity
            if fuel != self._fuel_main or cap != self._fuel_capacity:
                self._fuel_main = fuel
                self._fuel_capacity = cap
                self._update_display()
        except tk.TclError:
            self._poll_id = None

    @on("journal:FSDJump")
    def on_fsd_jump(self, ctx, data):
        self._current = data.get("StarSystem", "")
        self._jumps += 1
        self._total_dist += data.get("JumpDist", 0)
        self._update_display()
        self._save_state()

    @on("journal:Location")
    def on_location(self, ctx, data):
        self._current = data.get("StarSystem", "")
        self._update_display()

    @on("journal:NavRoute")
    def on_nav_route(self, ctx, data):
        self._read_navroute_json()
        self._update_display()

    @on("journal:NavRouteClear")
    def on_nav_route_clear(self, ctx, data):
        self._route = []
        self._navroute_mtime = 0
        self._update_display()
        self._update_route_text()

    @on("journal:StartJump")
    def on_start_jump(self, ctx, data):
        target = data.get("StarSystem", "")
        if target:
            try:
                self._lbl_system.config(
                    text=f"System: {self._current} → {target}", fg=ctx.accent
                )
            except tk.TclError:
                pass

    # ── Route helpers ─────────────────────────────────────────────────

    def _find_route_idx(self):
        for i, entry in enumerate(self._route):
            if entry["name"] == self._current:
                return i
        return -1

    def _route_remaining(self):
        if not self._route:
            return 0
        idx = self._find_route_idx()
        if idx >= 0:
            return len(self._route) - idx - 1
        return len(self._route)

    def _route_progress_pct(self):
        if len(self._route) < 2:
            return 0
        idx = self._find_route_idx()
        if idx < 0:
            return 0
        total = len(self._route) - 1
        if total <= 0:
            return 0
        return round(idx / total * 100)

    def _count_neutrons(self):
        idx = self._find_route_idx()
        if idx < 0:
            start = 0
        else:
            start = idx + 1
        count = 0
        for i in range(start, len(self._route)):
            if self._route[i].get("star_class") == "N":
                count += 1
        return count

    def _route_total_ly(self):
        if len(self._route) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(self._route)):
            a = self._route[i - 1].get("pos")
            b = self._route[i].get("pos")
            if a and b and len(a) >= 3 and len(b) >= 3:
                dx = b[0] - a[0]
                dy = b[1] - a[1]
                dz = b[2] - a[2]
                total += (dx * dx + dy * dy + dz * dz) ** 0.5
        return total

    # ── Display ───────────────────────────────────────────────────────

    def _adjust_width(self):
        self._ctx.win.update_idletasks()
        w = self._ctx.win.winfo_reqwidth()
        w = max(200, w + 14)
        self._ctx.set_width(w / self._ctx.scale_factor)
        self._ctx.resize()

    def _update_display(self):
        try:
            has_route = bool(self._route and len(self._route) >= 2)
            nav_dest = self._route[-1]["name"] if self._route else ""

            if self._current:
                if nav_dest:
                    sys_text = f"System: {self._current} → {nav_dest}"
                else:
                    sys_text = f"System: {self._current}"
            else:
                sys_text = "System: —"
            self._lbl_system.config(text=sys_text, fg=self._ctx.accent)

            left = self._route_remaining()
            pct = self._route_progress_pct()
            neutrons = self._count_neutrons()
            fuel_pct = (self._fuel_main / self._fuel_capacity * 100) if self._fuel_capacity > 0 else 0

            if has_route:
                route_ly = self._route_total_ly()
                self._lbl_left.config(
                    text=f"Jumps left: {left}  Fuel: {fuel_pct:.0f}%  Progress: {pct}%"
                )
                self._lbl_route_dist.config(text=f"Distance: {route_ly:.0f} ly")
            else:
                if self._fuel_capacity > 0:
                    fuel_text = f"Fuel: {fuel_pct:.0f}%"
                else:
                    fuel_text = "Fuel: --"
                self._lbl_left.config(text=fuel_text)
                self._lbl_route_dist.config(text="")

            if has_route and neutrons > 0:
                self._lbl_neutrons.config(text=f"\u26a1{neutrons}", fg="#4488ff")
            else:
                self._lbl_neutrons.config(text="", fg="#4488ff")

            self._update_next()
            self._adjust_width()
        except tk.TclError:
            self._poll_id = None

    def _get_next(self):
        idx = self._find_route_idx()
        if idx >= 0 and idx + 1 < len(self._route):
            return self._route[idx + 1]
        if idx < 0 and self._route:
            return self._route[0]
        return None

    def _update_next(self):
        try:
            nxt = self._get_next()
            if nxt:
                sc = nxt.get("star_class", "")
                if sc in SCOOPABLE:
                    self._lbl_next.config(text=f"S:[{sc}]", fg="#44cc44")
                elif sc == "N":
                    self._lbl_next.config(text=f"S:[{sc}]", fg="#4488ff")
                elif sc == "W":
                    self._lbl_next.config(text=f"S:[{sc}]", fg="#ff4444")
                else:
                    self._lbl_next.config(text=f"S:[{sc}]" if sc else "", fg="#888888")
            else:
                self._lbl_next.config(text="", fg="#888888")
        except tk.TclError:
            self._poll_id = None

    def _update_route_text(self):
        inner = getattr(self, "_settings_route_inner", None)
        if inner is None:
            return
        for w in inner.winfo_children():
            w.destroy()

        custom = bool(self._custom_route)
        source = self._custom_route if custom else self._route
        idx = self._find_route_idx() if not custom else -1
        bg = self._settings_bg
        fg = self._settings_fg
        font = self._settings_font

        if not source:
            tk.Label(inner, text="(no route plotted)", bg=bg, fg=fg, font=font).pack(anchor=tk.W)
            return

        max_name_len = max(len(e["name"]) for e in source) + 3

        for i, entry in enumerate(source):
            row = tk.Frame(inner, bg=bg)
            row.pack(fill=tk.X)

            marker = "\u2192" if (not custom and i == idx) else ""
            num = tk.Label(row, text=f"{marker}{i+1}.", width=5,
                           bg=bg, fg=fg, font=font, anchor=tk.W)
            num.pack(side=tk.LEFT)

            entry_w = tk.Entry(row, width=max_name_len, font=font,
                               bg="#1a1a1a", fg=fg,
                               readonlybackground="#1a1a1a",
                               relief=tk.FLAT, borderwidth=1)
            entry_w.insert(0, entry["name"])
            entry_w.config(state="readonly")
            def _select_all(e, ew=entry_w):
                ew.selection_range(0, tk.END)
                return "break"
            entry_w.bind("<Double-Button-1>", _select_all)
            entry_w.pack(side=tk.LEFT, padx=(4, 0))

            jumps = entry.get("jumps", 0)
            bodies = entry.get("bodies", [])
            body_count = (
                len(bodies) if isinstance(bodies, list)
                else entry.get("body_count", 0)
            )
            parts = []
            star_class = entry.get("star_class", "")
            if star_class:
                parts.append(f"[{star_class}]")
            if jumps:
                parts.append(f"{jumps}j")
            if body_count:
                parts.append(f"{body_count}b")
            info_text = "  ".join(parts)
            if info_text:
                lbl = tk.Label(row, text=info_text, bg=bg, fg="#888888", font=font)
                lbl.pack(side=tk.RIGHT, padx=(6, 0))

    def build_settings(self, parent, overlay, config):
        bg = config.get("overlay", "bg_color", default="#010101")
        fg = config.get("overlay", "fg_color", default="#e0e0e0")
        font = (config.get("overlay", "font_family", default="Consolas"), 10)
        accent = "#00d4aa"
        self._settings_parent = parent.winfo_toplevel()
        self._settings_bg = bg
        self._settings_fg = fg
        self._settings_font = font

        # ── File picker row ──
        row = tk.Frame(parent, bg=bg)
        row.pack(padx=12, pady=(12, 4), fill=tk.X)

        self._settings_btn_browse = tk.Button(
            row, text="Load Custom Route", font=font,
            bg="#2a2a2a", fg=fg, relief=tk.FLAT,
            activebackground="#3a3a3a", activeforeground=fg,
            command=self._pick_route_file,
        )
        self._settings_btn_browse.pack(side=tk.LEFT)

        right_frame = tk.Frame(row, bg=bg)
        right_frame.pack(side=tk.RIGHT)

        self._settings_btn_clear = tk.Button(
            right_frame, text="Clear", font=font,
            bg="#2a2a2a", fg="#cc4444", relief=tk.FLAT,
            activebackground="#3a3a3a", activeforeground="#ff6666",
            padx=10,
            command=self._clear_custom_route,
        )

        self._settings_lbl_path = tk.Label(
            row, text="", font=font, bg=bg, fg="#888888",
            anchor=tk.W, padx=8,
        )
        self._settings_lbl_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ── Route list ──
        tk.Label(
            parent, text="Route", font=font,
            bg=bg, fg=accent,
        ).pack(padx=12, pady=(12, 4), anchor=tk.W)

        inner = tk.Frame(parent, bg=bg)
        inner.pack(padx=12, pady=(0, 12), fill=tk.X)

        self._settings_route_inner = inner
        self._update_route_text()
        self._refresh_path_label()

    def _refresh_path_label(self):
        if hasattr(self, "_settings_lbl_path"):
            if self._custom_route:
                short = os.path.basename(self._custom_route_path)
                self._settings_lbl_path.config(text=short)
                self._settings_btn_clear.pack(side=tk.RIGHT)
            else:
                self._settings_lbl_path.config(text="(in-game NavRoute)")
                self._settings_btn_clear.pack_forget()

    @post_load
    def on_ready(self, ctx):
        self._journal_dir = _resolve_journal_path(ctx.config.get("journal_path"))
        self._recover_current_system()
        self._read_navroute_json()
        self._restore_custom_route()
        self._update_display()
        self._poll_id = 1
        self._poll_navroute()
