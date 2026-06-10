import tkinter as tk
from tkinter import ttk
import os
import json
import logging
from core.plugin_base import Plugin

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")

CAT_ORDER = ("Raw", "Manufactured", "Encoded")


class MaterialsTracker(Plugin):
    name = "Materials Tracker"
    version = "1.0.0"
    description = "Tracks engineering materials inventory"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.config = config
        self.game = game
        self._handler = self.on_event

        self.materials = {"Raw": {}, "Manufactured": {}, "Encoded": {}}
        self._ui_built = False
        self._parent = None
        self._tree = None
        self._info_label = None

        self._load()

        event_bus.subscribe("journal:Materials", self._handler)
        event_bus.subscribe("journal:MaterialCollected", self._handler)
        event_bus.subscribe("journal:MaterialDiscarded", self._handler)
        event_bus.subscribe("journal:MaterialTrade", self._handler)
        event_bus.subscribe("journal:EngineerCraft", self._handler)
        event_bus.subscribe("journal:Synthesis", self._handler)

    def on_unload(self):
        self._save()
        self._ui_built = False
        if self._parent:
            try:
                for w in self._parent.winfo_children():
                    w.destroy()
            except Exception:
                pass
        for ev in (
            "journal:Materials", "journal:MaterialCollected",
            "journal:MaterialDiscarded", "journal:MaterialTrade",
            "journal:EngineerCraft", "journal:Synthesis",
        ):
            self.event_bus.unsubscribe(ev, self._handler)

    def build_ui(self, parent):
        self._parent = parent
        font = (
            self.config.get("overlay", "font_family", default="Consolas"),
            self.config.get("overlay", "font_size", default=11),
        )
        font_small = (font[0], max(font[1] - 2, 8))
        font_bold = (font[0], font[1])
        bg = self.config.get("overlay", "bg_color", default="#000000")
        accent = self.config.get("overlay", "accent_color", default="#ffa500")
        fg = self.config.get("overlay", "fg_color", default="#e0e0e0")

        hdr = tk.Frame(parent, bg=bg)
        hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            hdr, text="Materials Inventory", font=font_bold, bg=bg, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT)

        self._info_label = tk.Label(
            parent, text="", font=font_small, bg=bg, fg="#888888", anchor=tk.W,
        )
        self._info_label.pack(fill=tk.X, pady=(0, 2))

        tree_frame = tk.Frame(parent, bg=bg)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(
            tree_frame, columns=("count",), show="tree headings",
            selectmode="none", style="Materials.Treeview",
        )
        self._tree.heading("#0", text="Material", anchor=tk.W)
        self._tree.heading("count", text="Count", anchor=tk.W)
        self._tree.column("#0", width=350, stretch=True)
        self._tree.column("count", width=80, stretch=False)

        tv_style = ttk.Style()
        tv_style.configure(
            "Materials.Treeview", background=bg, foreground=fg,
            fieldbackground=bg, font=font,
        )
        tv_style.map(
            "Materials.Treeview",
            background=[("selected", bg)],
            foreground=[("selected", fg)],
        )
        tv_style.configure(
            "Materials.Treeview.Heading", background=bg, foreground=accent,
            fieldbackground=bg, font=font_bold,
        )
        tv_style.map(
            "Materials.Treeview.Heading",
            background=[("active", bg)],
        )
        tv_style.configure("Vertical.TScrollbar", background=bg, troughcolor=bg,
                           arrowcolor=fg)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.configure(yscrollcommand=scr.set)

        self._tree.tag_configure("cat_raw", foreground=accent)
        self._tree.tag_configure("cat_manuf", foreground=accent)
        self._tree.tag_configure("cat_enc", foreground=accent)
        self._tree.tag_configure("count_tag", foreground="#888888")

        self._ui_built = True
        self._rebuild_tree()

    def _rebuild_tree(self):
        if not self._ui_built or not self._tree:
            return
        self._tree.delete(*self._tree.get_children())

        tag_map = {"Raw": "cat_raw", "Manufactured": "cat_manuf", "Encoded": "cat_enc"}

        total_count = 0
        total_items = 0

        for cat in CAT_ORDER:
            items = self.materials.get(cat, {})
            if not items:
                continue
            tag = tag_map[cat]
            cat_node = self._tree.insert(
                "", tk.END, text=cat, open=False,
                tags=(tag,),
            )

            cat_total = 0
            for mat_key in sorted(items.keys()):
                info = items[mat_key]
                dn = info.get("name", mat_key)
                c = info.get("count", 0)
                if c <= 0:
                    continue
                self._tree.insert(
                    cat_node, tk.END, text=dn,
                    values=(f"{c:,}",), tags=(tag,),
                )
                cat_total += c
                total_items += 1

            self._tree.set(cat_node, "count", f"{cat_total:,}")
            total_count += cat_total

        self._info_label.config(
            text=f"{total_items} unique materials, {total_count:,} total units"
        )

    def on_event(self, event, data):
        changed = False

        if event == "journal:Materials":
            for cat in CAT_ORDER:
                items = data.get(cat, [])
                for item in items:
                    name = item.get("Name", "")
                    count = item.get("Count", 0)
                    localised = item.get("Name_Localised", "")
                    if name:
                        self.materials[cat][name] = {
                            "name": self._display_name(name, localised),
                            "count": count,
                        }
            changed = True

        elif event == "journal:MaterialCollected":
            cat = data.get("Category", "")
            name = data.get("Name", "")
            count = data.get("Count", 0)
            localised = data.get("Name_Localised", "")
            if name:
                self._add_or_update(cat, name, count, localised)
                changed = True

        elif event == "journal:MaterialDiscarded":
            cat = data.get("Category", "")
            name = data.get("Name", "")
            count = data.get("Count", 0)
            if cat and name:
                self._deduct(name, count)
                changed = True

        elif event == "journal:MaterialTrade":
            cat = data.get("TraderType", "")
            disposed = data.get("MaterialDisposed", {})
            received = data.get("MaterialReceived", {})
            d_name = disposed.get("Name", "")
            d_count = disposed.get("Count", 0)
            if d_name:
                self._deduct(d_name, d_count)
            r_name = received.get("Name", "")
            r_count = received.get("Count", 0)
            r_localised = received.get("Name_Localised", "")
            if r_name and cat:
                self._add_or_update(cat, r_name, r_count, r_localised)
            if d_name or r_name:
                changed = True

        elif event in ("journal:EngineerCraft", "journal:Synthesis"):
            mats = data.get("Materials", [])
            for mat in mats:
                name = mat.get("Name", "")
                count = mat.get("Count", 0)
                if name:
                    self._deduct(name, count)
            if mats:
                changed = True

        if changed:
            self._save()
            self._rebuild_tree()

    def _add_or_update(self, category, name, count, localised=None):
        if category not in self.materials:
            return
        if name not in self.materials[category]:
            self.materials[category][name] = {
                "name": self._display_name(name, localised),
                "count": 0,
            }
        self.materials[category][name]["count"] += count
        if localised:
            self.materials[category][name]["name"] = localised

    def _deduct(self, name, count):
        for cat in self.materials.values():
            if name in cat:
                cat[name]["count"] = max(0, cat[name]["count"] - count)
                return True
        return False

    @staticmethod
    def _display_name(raw_name, localised=None):
        if localised:
            return localised
        s = raw_name.replace("_", " ")
        result = ""
        for i, c in enumerate(s):
            if i > 0 and c.isupper():
                result += " "
            result += c
        return result.title()

    @staticmethod
    def _data_path(name):
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, name)

    def _save(self):
        try:
            with open(self._data_path("materials.json"), "w", encoding="utf-8") as f:
                json.dump(self.materials, f, indent=2)
        except OSError as e:
            logger.error(f"materials save failed: {e}")

    def _load(self):
        path = self._data_path("materials.json")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    loaded = json.load(f)
                for cat in CAT_ORDER:
                    self.materials[cat] = loaded.get(cat, {})
            except (OSError, json.JSONDecodeError):
                pass
