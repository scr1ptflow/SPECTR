import tkinter as tk
from tkinter import ttk
import os
import json
import urllib.request
import urllib.parse
import logging
from core.plugin_base import Plugin
from core.threads import submit as _api_submit
from core.journal import default_journal_path, read_last_journal_event

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
CODEX_REF_URL = "https://us-central1-canonn-api-236217.cloudfunctions.net/query/codex/ref"
CHALLENGE_URL = "https://us-central1-canonn-api-236217.cloudfunctions.net/query/challenge/status"


class CodexBingo(Plugin):
    name = "Codex Bingo"
    version = "1.0.0"
    description = "Codex exploration tracker grouped by region and category"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.config = config
        self.game = game
        self.status = status
        self._handler = self.on_event

        self._journal_dir = default_journal_path(config.get("journal_path"))

        self._codex_ref = {}
        self._entries_by_region = {}
        self._codex_firsts = {}
        self._commander_fid = ""
        self._commander_name = ""
        self._ref_loaded = False
        self._ui_built = False
        self._parent = None

        self._load_codex_ref()
        self._restore_state()

        event_bus.subscribe("journal:CodexEntry", self._handler)
        event_bus.subscribe("journal:LoadGame", self._handler)

    def on_unload(self):
        self.event_bus.unsubscribe("journal:CodexEntry", self._handler)
        self.event_bus.unsubscribe("journal:LoadGame", self._handler)
        self._ui_built = False
        if self._parent:
            try:
                for w in self._parent.winfo_children():
                    w.destroy()
            except Exception:
                pass

    def build_ui(self, parent):
        self._parent = parent
        font = (
            self.config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        font_small = (font[0], max(font[1] - 2, 8))
        font_bold = (font[0], font[1])
        bg = self.config.get("overlay", "bg_color", default="#000000")
        accent = self.config.get("overlay", "accent_color", default="#ffa500")
        fg = self.config.get("overlay", "fg_color", default="#e0e0e0")

        hdr = tk.Frame(parent, bg=bg)
        hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            hdr, text="Codex Bingo", font=font_bold, bg=bg, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT)
        self.import_btn = tk.Button(
            hdr, text="Import Challenge", font=font_small,
            bg=bg, fg=fg, command=self._import_challenge,
        )
        self.import_btn.pack(side=tk.RIGHT, padx=(2, 0))

        self.info_label = tk.Label(
            parent, text="", font=font_small, bg=bg, fg="#888888", anchor=tk.W,
        )
        self.info_label.pack(fill=tk.X, pady=(0, 2))

        tree_frame = tk.Frame(parent, bg=bg)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame, columns=("status",), show="tree headings",
            selectmode="none", style="CodexBingo.Treeview",
        )
        self.tree.heading("#0", text="Entry", anchor=tk.W)
        self.tree.heading("status", text="", anchor=tk.W)
        self.tree.column("#0", width=350, stretch=True)
        self.tree.column("status", width=100, stretch=False)

        tv_style = ttk.Style()
        tv_style.configure(
            "CodexBingo.Treeview", background=bg, foreground=fg,
            fieldbackground=bg, font=font,
        )
        tv_style.map(
            "CodexBingo.Treeview",
            background=[("selected", bg)],
            foreground=[("selected", fg)],
        )
        tv_style.configure(
            "CodexBingo.Treeview.Heading", background=bg, foreground=accent,
            fieldbackground=bg, font=font_bold,
        )
        tv_style.map(
            "CodexBingo.Treeview.Heading",
            background=[("active", bg)],
        )
        tv_style.configure("Vertical.TScrollbar", background=bg, troughcolor=bg,
                           arrowcolor=fg)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scr.set)

        self.tree.tag_configure("unscanned", foreground="#ffffff")
        self.tree.tag_configure("partial", foreground="#ffaa00")
        self.tree.tag_configure("complete", foreground="#00ff00")

        self._ui_built = True
        self._rebuild_tree()

    def on_event(self, event, data):
        if event == "journal:CodexEntry":
            eid = data.get("EntryID")
            if eid and str(eid) not in self._codex_firsts:
                self._codex_firsts[str(eid)] = {
                    "entryid": eid,
                    "timestamp": data.get("timestamp", ""),
                    "is_new": data.get("IsNewEntry", False),
                    "category": data.get("Category_Localised") or "",
                    "subcategory": data.get("SubCategory_Localised") or "",
                    "name": data.get("Name_Localised") or data.get("Name", ""),
                }
                self._save_codex_firsts()
                self._rebuild_tree()
        elif event == "journal:LoadGame":
            fid = data.get("FID", "")
            if fid and fid != self._commander_fid:
                self._commander_fid = fid
                self._commander_name = data.get("Commander", "")
                self._load_codex_firsts()
                self._rebuild_tree()

    @staticmethod
    def _data_path(name):
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, name)

    def _save_json(self, name, obj):
        try:
            with open(self._data_path(name), "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2)
        except OSError as e:
            logger.error(f"save {name} failed: {e}")

    def _load_json(self, name, default=None):
        path = self._data_path(name)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return default if default is not None else {}

    def _load_codex_ref(self):
        entries = self._load_json("codexRef.json", [])
        if entries:
            self._build_ref_index(entries)
            self._rebuild_tree()
        self._fetch_codex_ref()

    def _fetch_codex_ref(self):
        def do_fetch():
            try:
                req = urllib.request.Request(
                    CODEX_REF_URL, headers={"User-Agent": "EDOverlay/2.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = json.loads(resp.read())
                if isinstance(raw, dict):
                    entries = [v for v in raw.values() if isinstance(v, dict)]
                elif isinstance(raw, list):
                    entries = raw
                else:
                    entries = []
                self._save_json("codexRef.json", entries)
                self._build_ref_index(entries)
                self._schedule(0, self._rebuild_tree)
            except Exception as e:
                logger.error(f"codexRef fetch: {e}")
                err_msg = str(e)[:80]
                self._schedule(0, lambda: self._show_fetch_error(err_msg))
        _api_submit(do_fetch)

    def _show_fetch_error(self, msg):
        if not self._ui_built:
            return
        self.info_label.config(text=f"Fetch failed: {msg}")

    def _build_ref_index(self, entries):
        self._codex_ref = {}
        self._entries_by_region = {}
        for entry in entries:
            eid = entry.get("entryid")
            if eid is None:
                continue
            eid = str(eid)
            self._codex_ref[eid] = entry
            category = entry.get("hud_category") or "Unknown"
            sub_class = entry.get("sub_class") or "Unknown"
            name = entry.get("english_name", f"Entry {eid}")
            if category not in self._entries_by_region:
                self._entries_by_region[category] = {}
            if sub_class not in self._entries_by_region[category]:
                self._entries_by_region[category][sub_class] = []
            self._entries_by_region[category][sub_class].append({
                "entryid": eid,
                "name": name,
            })
        self._ref_loaded = True

    def _restore_state(self):
        entry = read_last_journal_event(self._journal_dir, ("LoadGame",))
        if entry:
            self._commander_fid = entry.get("FID", "")
            self._commander_name = entry.get("Commander", "")
        self._load_codex_firsts()

    def _load_codex_firsts(self):
        if not self._commander_fid:
            self._codex_firsts = {}
            return
        data = self._load_json(f"{self._commander_fid}-codex.json")
        self._codex_firsts = data if isinstance(data, dict) else {}

    def _save_codex_firsts(self):
        if self._commander_fid:
            self._save_json(
                f"{self._commander_fid}-codex.json", self._codex_firsts
            )

    def _scan_all_codex_entries(self):
        import glob
        if not os.path.isdir(self._journal_dir):
            return 0, {}
        pattern = os.path.join(self._journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        new_entries = {}
        count = 0
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if data.get("event") != "CodexEntry":
                            continue
                        eid = data.get("EntryID")
                        if not eid or str(eid) in self._codex_firsts:
                            continue
                        entry = {
                            "entryid": eid,
                            "timestamp": data.get("timestamp", ""),
                            "is_new": data.get("IsNewEntry", False),
                            "category": data.get("Category_Localised") or "",
                            "subcategory": data.get("SubCategory_Localised") or "",
                            "name": data.get("Name_Localised") or data.get("Name", ""),
                        }
                        new_entries[str(eid)] = entry
                        count += 1
            except OSError as e:
                logger.warning(f"Failed to read journal {filepath}: {e}")
        return count, new_entries

    def _schedule(self, ms, cb):
        if self._parent:
            try:
                self._parent.after(ms, cb)
            except Exception:
                pass
        elif self.overlay:
            self.overlay.schedule(ms, cb)

    def _rebuild_tree(self):
        if not self._ui_built:
            return
        self.tree.delete(*self.tree.get_children())
        if not self._ref_loaded:
            self.info_label.config(text="Loading codex reference...")
            return

        total_entries = 0
        total_scanned = 0

        for cat_name in sorted(self._entries_by_region.keys()):
            cat_node = self.tree.insert("", tk.END, text=cat_name, open=False)
            sub_classes = self._entries_by_region[cat_name]
            cat_total = 0
            cat_scanned = 0

            for sub_name in sorted(sub_classes.keys()):
                entries = sub_classes[sub_name]
                entries.sort(key=lambda e: e["name"].lower())
                sub_node = self.tree.insert(
                    cat_node, tk.END, text=sub_name, open=False,
                )
                sub_total = 0
                sub_scanned = 0

                for entry in entries:
                    eid = str(entry["entryid"])
                    scanned = eid in self._codex_firsts
                    tag = "complete" if scanned else "unscanned"
                    status_text = "\u2713" if scanned else ""
                    self.tree.insert(
                        sub_node, tk.END, text=entry["name"],
                        values=(status_text,), tags=(tag,),
                    )
                    total_entries += 1
                    sub_total += 1
                    if scanned:
                        total_scanned += 1
                        sub_scanned += 1

                sub_pct = f"{100 * sub_scanned // sub_total}%" if sub_total else "0%"
                self.tree.item(sub_node, text=f"{sub_name} ({sub_scanned}/{sub_total}, {sub_pct})")
                sub_tag = "unscanned"
                if sub_scanned > 0:
                    sub_tag = "partial" if sub_scanned < sub_total else "complete"
                self.tree.item(sub_node, tags=(sub_tag,))
                cat_total += sub_total
                cat_scanned += sub_scanned

            cat_pct = f"{100 * cat_scanned // cat_total}%" if cat_total else "0%"
            self.tree.item(cat_node, text=f"{cat_name} ({cat_scanned}/{cat_total}, {cat_pct})")
            cat_tag = "unscanned"
            if cat_scanned > 0:
                cat_tag = "partial" if cat_scanned < cat_total else "complete"
            self.tree.item(cat_node, tags=(cat_tag,))



        self.info_label.config(
            text=f"Scanned: {total_scanned} / {total_entries}"
        )

    def _import_challenge(self):
        if not self._commander_name:
            self.info_label.config(text="No commander name available")
            return
        self.info_label.config(text="Importing challenge + scanning journal...")
        self.import_btn.config(state=tk.DISABLED)
        _api_submit(self._do_import_challenge)

    def _do_import_challenge(self):
        journal_count, journal_entries = self._scan_all_codex_entries()

        url = (
            f"{CHALLENGE_URL}?cmdr={urllib.parse.quote(self._commander_name)}"
        )
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "EDOverlay/2.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            if isinstance(data, dict):
                items = list(data.items())
            elif isinstance(data, list):
                items = [(str(e.get("entryid", "")), e) for e in data]
            else:
                items = []

            challenge_entries = {}
            for eid_str, entry in items:
                if eid_str and eid_str not in self._codex_firsts:
                    challenge_entries[eid_str] = {
                        "entryid": (
                            int(eid_str) if eid_str.isdigit() else eid_str
                        ),
                        "timestamp": entry.get("timestamp", ""),
                        "is_new": entry.get("isNew", False),
                        "source": "challenge_import",
                    }

            total = journal_count + len(challenge_entries)
            self._schedule(0, lambda je=journal_entries, ce=challenge_entries, t=total: self._apply_imported(je, ce, t))
        except Exception as e:
            logger.error(f"Challenge import failed: {e}")
            err_msg = str(e)[:80]
            self._schedule(0, lambda: self._on_import_error(err_msg))

    def _apply_imported(self, journal_entries, challenge_entries, total):
        self._codex_firsts.update(journal_entries)
        self._codex_firsts.update(challenge_entries)
        self._save_codex_firsts()
        self._on_import_done(total)

    def _on_import_done(self, count):
        self.import_btn.config(state=tk.NORMAL)
        self._rebuild_tree()
        self.info_label.config(text=f"Import complete: {count} new entries")

    def _on_import_error(self, msg):
        self.import_btn.config(state=tk.NORMAL)
        self.info_label.config(text=f"Import failed: {msg}")
