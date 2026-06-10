import tkinter as tk
from tkinter import ttk
from core.plugin_base import Plugin


class PluginManagerUI(Plugin):
    name = "Plugin Manager"
    version = "1.0.0"
    description = "Toggle plugins on/off and configure API keys"

    API_KEY_FIELDS = [
        ("edsm_key", "EDSM API Key"),
        ("inara_key", "Inara API Key"),
    ]

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._config = config
        self._pm = getattr(overlay, "plugin_manager", None)

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            config.get("overlay", "font_size", default=11),
        )
        font_small = (font[0], max(font[1] - 2, 8))
        bg = config.get("overlay", "bg_color", default="#000000")
        fg = config.get("overlay", "fg_color", default="#e0e0e0")

        self._bg = bg

        self.win = tk.Toplevel()
        self.win.title("SPECTR - Settings")
        self.win.configure(bg=bg)
        self.win.geometry("500x600+50+50")
        self.win.resizable(True, True)
        self.win.attributes("-topmost", True)

        style = ttk.Style()
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=bg, foreground=fg,
                        padding=[8, 2])
        style.map("TNotebook.Tab",
                  background=[("selected", bg), ("active", bg)],
                  foreground=[("selected", fg), ("active", fg)])

        notebook = ttk.Notebook(self.win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_settings_tab(notebook, font, bg, fg)
        self._build_compass_tab(notebook, font, bg, fg)

        self._build_codex_tab(notebook, font, bg, fg)
        self._build_materials_tab(notebook, font, bg, fg)
        self._build_plugins_tab(notebook, font, bg, fg)
        self._build_apis_tab(notebook, font, font_small, bg, fg)



        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.iconify()

    def _build_settings_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Settings")
        tk.Label(
            tab, text="Settings", font=font,
            bg=bg, fg="#00d4aa",
        ).pack(padx=12, pady=(12, 0), anchor=tk.W)

        self._hide_var = tk.BooleanVar(
            value=self._config.get("overlay", "hide_on_unfocus", default=True)
        )
        cb = tk.Checkbutton(
            tab, text="Hide overlays when game not focused",
            variable=self._hide_var,
            bg=bg, fg=fg, selectcolor=bg,
            activebackground=bg, activeforeground="#ffffff",
            font=font, anchor=tk.W,
            command=self._toggle_hide_on_unfocus,
        )
        cb.pack(fill=tk.X, padx=12, pady=(12, 0))

    def _build_plugins_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Plugins")

        container = tk.Frame(tab, bg=bg)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 4))

        self._checkboxes = {}
        self._vars = {}
        self._cb_container = container

        self._refresh_plugins()

        note = tk.Label(
            tab,
            text="Uncheck a plugin to disable it immediately.\nCheck to re-enable.",
            font=font, bg=bg, fg="#666666", anchor=tk.W, justify=tk.LEFT,
        )
        note.pack(fill=tk.X, padx=12, pady=(4, 0))

    def _build_apis_tab(self, notebook, font, font_small, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="API Keys")

        self._api_entries = {}
        row = 0
        for key, label in self.API_KEY_FIELDS:
            lbl = tk.Label(
                tab, text=label, font=font, bg=bg, fg="#00d4aa", anchor=tk.W,
            )
            lbl.grid(row=row, column=0, sticky=tk.W, padx=12, pady=(8, 0))
            row += 1
            val = self._config.get("api_keys", key, default="")
            entry = tk.Entry(
                tab, font=font, bg="#2a2a4e", fg="#e0e0e0",
                insertbackground="#e0e0e0", relief=tk.FLAT, bd=4,
            )
            entry.insert(0, val)
            entry.grid(row=row, column=0, sticky=tk.EW, padx=12, pady=(2, 4))
            self._api_entries[key] = entry
            row += 1

        tk.Grid.columnconfigure(tab, 0, weight=1)

        info = tk.Label(
            tab,
            text="Get your API keys from:\nedsm.net -> My Account -> API Key\ninara.cz -> Community -> API",
            font=font_small, bg=bg, fg="#666666", anchor=tk.W, justify=tk.LEFT,
        )
        info.grid(row=row, column=0, sticky=tk.W, padx=12, pady=(8, 0))
        row += 1

        btn_frame = tk.Frame(tab, bg=bg)
        btn_frame.grid(row=row, column=0, pady=(12, 4))

        self._save_status = tk.Label(
            btn_frame, text="", font=font, bg=bg, fg="#44aa44",
        )
        self._save_status.pack(pady=(0, 4))

        save_btn = tk.Button(
            btn_frame, text="Save", font=font,
            bg="#2a6e3a", fg="#e0e0e0", relief=tk.FLAT, padx=20, pady=4,
            command=self._save_apis,
        )
        save_btn.pack()

    def _build_codex_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Codex Bingo")

        if not self._pm:
            tk.Label(
                tab, text="Plugin manager unavailable", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        cb = self._pm.get_plugin("Codex Bingo")
        if not cb or not hasattr(cb, "build_ui"):
            tk.Label(
                tab, text="Codex Bingo plugin not loaded", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        cb.build_ui(tab)

    def _build_materials_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Materials")

        if not self._pm:
            tk.Label(
                tab, text="Plugin manager unavailable", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        mt = self._pm.get_plugin("Materials Tracker")
        if not mt or not hasattr(mt, "build_ui"):
            tk.Label(
                tab, text="Materials Tracker plugin not loaded", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        mt.build_ui(tab)

    def _build_compass_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Compass")

        if not self._pm:
            tk.Label(
                tab, text="Plugin manager unavailable", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        cp = self._pm.get_plugin("Compass")
        if not cp or not hasattr(cp, "set_target") or not hasattr(cp, "clear_target"):
            tk.Label(
                tab, text="Compass plugin not loaded", font=font,
                bg=bg, fg="#ff4444",
            ).pack(pady=20)
            return

        accent = "#00d4aa"

        lat_frame = tk.Frame(tab, bg=bg)
        lat_frame.pack(fill=tk.X, padx=12, pady=(10, 0))
        tk.Label(
            lat_frame, text="Latitude", font=font, bg=bg, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT)
        self._compass_lat = tk.Entry(
            lat_frame, font=font, bg="#2a2a4e", fg="#e0e0e0",
            insertbackground="#e0e0e0", relief=tk.FLAT, bd=4,
        )
        self._compass_lat.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))
        if cp.target_lat is not None:
            self._compass_lat.insert(0, str(cp.target_lat))

        lon_frame = tk.Frame(tab, bg=bg)
        lon_frame.pack(fill=tk.X, padx=12, pady=(6, 0))
        tk.Label(
            lon_frame, text="Longitude", font=font, bg=bg, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT)
        self._compass_lon = tk.Entry(
            lon_frame, font=font, bg="#2a2a4e", fg="#e0e0e0",
            insertbackground="#e0e0e0", relief=tk.FLAT, bd=4,
        )
        self._compass_lon.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))
        if cp.target_lon is not None:
            self._compass_lon.insert(0, str(cp.target_lon))

        name_frame = tk.Frame(tab, bg=bg)
        name_frame.pack(fill=tk.X, padx=12, pady=(6, 0))
        tk.Label(
            name_frame, text="Name (opt)", font=font, bg=bg, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT)
        self._compass_name = tk.Entry(
            name_frame, font=font, bg="#2a2a4e", fg="#e0e0e0",
            insertbackground="#e0e0e0", relief=tk.FLAT, bd=4,
        )
        self._compass_name.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))
        if cp.target_name:
            self._compass_name.insert(0, cp.target_name)

        self._compass_status = tk.Label(
            tab, text="", font=font, bg=bg, fg=accent,
        )
        self._compass_status.pack(pady=(8, 0))

        btn_frame = tk.Frame(tab, bg=bg)
        btn_frame.pack(pady=(6, 4))

        tk.Button(
            btn_frame, text="Set Target", font=font,
            bg="#2a6e3a", fg="#e0e0e0", relief=tk.FLAT, padx=16, pady=4,
            command=lambda: self._set_compass_target(cp),
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="Clear Target", font=font,
            bg="#6e2a2a", fg="#e0e0e0", relief=tk.FLAT, padx=16, pady=4,
            command=lambda: self._clear_compass_target(cp),
        ).pack(side=tk.LEFT, padx=4)

        self._update_compass_status(cp)

    def _set_compass_target(self, cp):
        try:
            lat = float(self._compass_lat.get().strip())
            lon = float(self._compass_lon.get().strip())
            name = self._compass_name.get().strip()
            cp.set_target(lat, lon, name)
            self._compass_status.config(text="Target set!")
        except ValueError:
            self._compass_status.config(text="Invalid lat/lon values", fg="#ff4444")
            return
        self._compass_status.config(fg="#44aa44")
        self.win.after(2000, lambda: self._compass_status.config(text=""))

    def _clear_compass_target(self, cp):
        cp.clear_target()
        self._compass_lat.delete(0, tk.END)
        self._compass_lon.delete(0, tk.END)
        self._compass_name.delete(0, tk.END)
        self._compass_status.config(text="Target cleared", fg="#888888")
        self.win.after(2000, lambda: self._compass_status.config(text=""))

    def _update_compass_status(self, cp):
        if cp.target_lat is not None and cp.target_lon is not None:
            name_part = f" ({cp.target_name})" if cp.target_name else ""
            self._compass_status.config(
                text=f"Current: {cp.target_lat:.4f}, {cp.target_lon:.4f}{name_part}",
                fg="#44aa44",
            )
        else:
            self._compass_status.config(text="No target set", fg="#888888")

    def _save_apis(self):
        api_data = {}
        for key, entry in self._api_entries.items():
            api_data[key] = entry.get().strip()
        self._config.data["api_keys"] = api_data
        self._config.save()
        self._save_status.config(text="Saved!")
        self.win.after(2000, lambda: self._save_status.config(text=""))

    def _on_close(self):
        self.win.destroy()
        self.overlay.root.after(0, self.overlay._on_close)

    def _toggle_hide_on_unfocus(self):
        self._config.data.setdefault("overlay", {})["hide_on_unfocus"] = self._hide_var.get()
        self._config.save()

    def _refresh_plugins(self):
        for w in self._checkboxes.values():
            w.destroy()
        self._checkboxes.clear()
        self._vars.clear()

        if not self._pm:
            return

        for pname in self._pm._name_to_dir:
            if pname in ("Plugin Manager", "Codex Bingo", "Materials Tracker"):
                continue
            plugin_cfg = self._config.plugin_config(pname)
            enabled = plugin_cfg.get("enabled", True)
            var = tk.BooleanVar(value=enabled)
            cb = tk.Checkbutton(
                self._cb_container, text=pname, variable=var,
                bg=self._bg, fg="#e0e0e0", selectcolor=self._bg,
                activebackground=self._bg, activeforeground="#ffffff",
                font=("Consolas", 11), anchor=tk.W,
                command=lambda n=pname, v=var: self._toggle(n, v),
            )
            cb.pack(fill=tk.X, pady=1)
            self._checkboxes[pname] = cb
            self._vars[pname] = var

    def _toggle(self, name, var):
        if not self._pm:
            return
        if var.get():
            self._pm.load_plugin(name, self.overlay, self.event_bus,
                                  self.overlay.config, self.game, self.status)
        else:
            self._pm.unload_plugin(name, self.overlay)
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["enabled"] = var.get()
        self._config.save()

    def on_unload(self):
        pass
