import tkinter as tk
from tkinter import font as tkfont
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
            self.overlay._scaled_font_size,
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
            tab, text="Auto-hide when game loses focus",
            variable=self._hide_var,
            bg=bg, fg=fg, selectcolor=bg,
            activebackground=bg, activeforeground="#ffffff",
            font=font, anchor=tk.W,
            command=self._toggle_hide_on_unfocus,
        )
        cb.pack(fill=tk.X, padx=12, pady=(12, 0))

        opacity_frame = tk.Frame(tab, bg=bg)
        opacity_frame.pack(fill=tk.X, padx=12, pady=(14, 0))
        tk.Label(
            opacity_frame, text="Opacity", font=font,
            bg=bg, fg=fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        self._opacity_var = tk.DoubleVar(
            value=self._config.get("overlay", "opacity", default=1.0)
        )
        scale = tk.Scale(
            opacity_frame, from_=0.05, to=1.0, resolution=0.05,
            orient=tk.HORIZONTAL, variable=self._opacity_var,
            bg=bg, fg=fg, troughcolor="#1a1a1a",
            activebackground="#00d4aa", highlightbackground=bg,
            font=font, length=200,
            command=self._on_opacity_change,
        )
        scale.pack(side=tk.RIGHT)

        font_frame = tk.Frame(tab, bg=bg)
        font_frame.pack(fill=tk.X, padx=12, pady=(14, 0))
        tk.Label(
            font_frame, text="Font", font=font,
            bg=bg, fg=fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        all_fonts = sorted(tkfont.families())
        current_font = self._config.get("overlay", "font_family", default="Consolas")
        self._font_var = tk.StringVar(value=current_font)
        font_box = ttk.Combobox(
            font_frame, textvariable=self._font_var,
            values=all_fonts, state="readonly",
            font=("Consolas", 10), width=28,
        )
        font_box.pack(side=tk.RIGHT)
        font_box.bind("<<ComboboxSelected>>", self._on_font_change)



    def _build_plugins_tab(self, notebook, font, bg, fg):
        tab = tk.Frame(notebook, bg=bg)
        notebook.add(tab, text="Plugins")

        container = tk.Frame(tab, bg=bg)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 4))

        self._checkboxes = {}
        self._vars = {}
        self._dynamic_cbs = {}
        self._dynamic_vars = {}
        self._pos_cells = {}
        self._cb_container = container

        sep_color = "#333333"
        hdr_fg = "#777777"

        # Header — grid layout so vertical separators are continuous
        hdr_frame = tk.Frame(container, bg=bg)
        hdr_frame.pack(fill=tk.X, pady=(0, 2))

        hdr_frame.columnconfigure(0, minsize=28)  # All + toggle
        hdr_frame.columnconfigure(1, minsize=1)   # sep
        hdr_frame.columnconfigure(2, minsize=58)  # Dynamic + toggle
        hdr_frame.columnconfigure(3, minsize=1)   # sep
        hdr_frame.columnconfigure(4, weight=1)    # Plugin
        hdr_frame.columnconfigure(5, minsize=1)   # sep
        hdr_frame.columnconfigure(6, minsize=68)  # Position

        # Row 0: column labels
        tk.Label(hdr_frame, text="All", bg=bg, fg=hdr_fg, font=("Consolas", 9)).grid(row=0, column=0, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(row=0, column=1, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Dynamic", bg=bg, fg=hdr_fg, font=("Consolas", 9)).grid(row=0, column=2, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(row=0, column=3, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Plugin", bg=bg, fg=hdr_fg, font=("Consolas", 9), anchor=tk.W).grid(row=0, column=4, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(row=0, column=5, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Position", bg=bg, fg=hdr_fg, font=("Consolas", 9)).grid(row=0, column=6, sticky=tk.W)

        # Row 1: toggle-all squares
        self._toggle_all_var = tk.BooleanVar()
        self._toggle_all_btn = tk.Checkbutton(
            hdr_frame, text="", variable=self._toggle_all_var,
            bg=bg, fg="#e0e0e0", selectcolor=bg,
            activebackground=bg, activeforeground="#ffffff",
            command=self._toggle_all_enabled,
        )
        self._toggle_all_btn.grid(row=1, column=0, sticky=tk.W)

        self._toggle_all_dy_var = tk.BooleanVar()
        self._toggle_all_dy_btn = tk.Checkbutton(
            hdr_frame, text="", variable=self._toggle_all_dy_var,
            bg=bg, fg="#e0e0e0", selectcolor=bg,
            activebackground=bg, activeforeground="#ffffff",
            command=self._toggle_all_dynamic,
        )
        self._toggle_all_dy_btn.grid(row=1, column=2, sticky=tk.W)

        self._refresh_plugins()

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
                tab, font=font, bg="#1a1a1a", fg="#e0e0e0",
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
            lat_frame, font=font, bg="#1a1a1a", fg="#e0e0e0",
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
            lon_frame, font=font, bg="#1a1a1a", fg="#e0e0e0",
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
            name_frame, font=font, bg="#1a1a1a", fg="#e0e0e0",
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

    def _on_opacity_change(self, val):
        try:
            opacity = float(val)
            self.overlay.root.attributes("-alpha", opacity)
            self._config.data.setdefault("overlay", {})["opacity"] = opacity
            self._config.save()
        except Exception:
            pass

    def _on_font_change(self, event=None):
        font_family = self._font_var.get()
        self._config.data.setdefault("overlay", {})["font_family"] = font_family
        self._config.save()
        self.overlay._setup_styles()
        self.overlay._reapply_font()

    def _toggle_hide_on_unfocus(self):
        self._config.data.setdefault("overlay", {})["hide_on_unfocus"] = self._hide_var.get()
        self._config.save()

    def _refresh_plugins(self):
        for w in self._checkboxes.values():
            w.destroy()
        self._checkboxes.clear()
        self._vars.clear()
        for w in self._dynamic_cbs.values():
            w.destroy()
        self._dynamic_cbs.clear()
        self._dynamic_vars.clear()
        self._pos_cells.clear()

        if not self._pm:
            return

        sep_color = "#333333"
        pos_grid_names = [
            "top-left", "top", "top-right",
            "center-left", "center", "center-right",
            "bottom-left", "bottom", "bottom-right",
        ]

        first = True
        for pname in self._pm._name_to_dir:
            if pname in ("Plugin Manager", "Codex Bingo", "Materials Tracker"):
                continue

            plugin_cfg = self._config.plugin_config(pname)
            enabled = plugin_cfg.get("enabled", True)
            dynamic = plugin_cfg.get("dynamic", False)
            pos_current = plugin_cfg.get("window_position", "")

            # Horizontal separator between rows
            if not first:
                tk.Frame(self._cb_container, bg=sep_color, height=1).pack(fill=tk.X)
            first = False

            row = tk.Frame(self._cb_container, bg=self._bg)
            row.pack(fill=tk.X, pady=1)

            en_var = tk.BooleanVar(value=enabled)
            en_cb = tk.Checkbutton(
                row, text="", variable=en_var,
                bg=self._bg, fg="#e0e0e0", selectcolor=self._bg,
                activebackground=self._bg, activeforeground="#ffffff",
                command=lambda n=pname, v=en_var: self._toggle(n, v),
            )
            en_cb.pack(side=tk.LEFT)

            tk.Frame(row, bg=sep_color, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            dy_var = tk.BooleanVar(value=dynamic)
            dy_cb = tk.Checkbutton(
                row, text="", variable=dy_var,
                bg=self._bg, fg="#e0e0e0", selectcolor="#1a1a1a",
                activebackground=self._bg, activeforeground="#ffffff",
                command=lambda n=pname, v=dy_var: self._toggle_dynamic(n, v),
            )
            dy_cb.pack(side=tk.LEFT, padx=(4, 0))

            tk.Frame(row, bg=sep_color, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            lbl = tk.Label(
                row, text=pname, bg=self._bg, fg="#e0e0e0",
                font=("Consolas", 11), anchor=tk.W,
            )
            lbl.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)

            tk.Frame(row, bg=sep_color, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            # 3x3 position grid
            pos_frame = tk.Frame(row, bg=self._bg)
            pos_frame.pack(side=tk.LEFT, padx=(4, 0))

            cells = {}
            for i, pos in enumerate(pos_grid_names):
                r, c = divmod(i, 3)
                is_sel = pos == pos_current
                cell = tk.Label(
                    pos_frame, text=" ", width=2, bd=1, relief=tk.SOLID,
                    bg="#00d4aa" if is_sel else "#333333",
                )
                cell.grid(row=r, column=c, padx=1, pady=1)
                cell.bind(
                    "<Button-1>",
                    lambda e, n=pname, p=pos: self._toggle_position(n, p),
                )
                cells[pos] = cell

            self._checkboxes[pname] = en_cb
            self._vars[pname] = en_var
            self._dynamic_cbs[pname] = dy_cb
            self._dynamic_vars[pname] = dy_var
            self._pos_cells[pname] = cells

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

    def _toggle_dynamic(self, name, var):
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["dynamic"] = var.get()
        self._config.save()

    def _toggle_position(self, name, pos):
        cells = self._pos_cells.get(name)
        if not cells:
            return
        for p, cell in cells.items():
            cell.config(bg="#00d4aa" if p == pos else "#333333")
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["window_position"] = pos
        self._config.save()
        self.overlay.reposition_plugin(name, pos)

    def _toggle_all_enabled(self):
        if not self._pm:
            return
        names = [n for n in self._pm._name_to_dir
                 if n not in ("Plugin Manager", "Codex Bingo", "Materials Tracker")]
        if not names:
            return
        all_on = all(self._vars.get(n, tk.BooleanVar()).get() for n in names)
        new_val = not all_on
        for n in names:
            v = self._vars.get(n)
            if v is None:
                continue
            v.set(new_val)
            self._toggle(n, v)
        self._toggle_all_var.set(new_val)

    def _toggle_all_dynamic(self):
        if not self._pm:
            return
        names = [n for n in self._pm._name_to_dir
                 if n not in ("Plugin Manager", "Codex Bingo", "Materials Tracker")]
        if not names:
            return
        all_on = all(self._dynamic_vars.get(n, tk.BooleanVar()).get() for n in names)
        new_val = not all_on
        for n in names:
            v = self._dynamic_vars.get(n)
            if v is None:
                continue
            v.set(new_val)
            self._toggle_dynamic(n, v)
        self._toggle_all_dy_var.set(new_val)

    def on_unload(self):
        pass
