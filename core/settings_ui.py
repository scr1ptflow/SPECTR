import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from .overlay import _set_console_visibility

ACCENT = "#00d4aa"


def open_settings(overlay, event_bus, config, game=None, status=None, journal=None):
    """Open the SPECTR settings window."""
    ui = SettingsUI()
    ui.on_load(overlay, event_bus, config, game, status, journal)
    return ui


class SettingsUI:

    API_KEY_FIELDS = [
        ("edsm_key", "EDSM API Key"),
        ("inara_key", "Inara API Key"),
    ]

    def on_load(self, overlay, event_bus, config, game=None, status=None, journal=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._journal = journal
        self._config = config
        self._pm = getattr(overlay, "plugin_manager", None)

        self._bg = config.get("overlay", "bg_color", default="#000000")
        fg = config.get("overlay", "fg_color", default="#e0e0e0")
        self._fg = fg
        self._font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        self._font_small = (self._font[0], max(self._font[1] - 2, 8))

        self.win = tk.Toplevel()
        self.win.title("SPECTR - Settings")
        self.win.configure(bg=self._bg)

        saved_geo = self._config.get("overlay", "settings_geometry", default=None)
        if saved_geo:
            self.win.geometry(saved_geo)
        else:
            self.win.geometry("550x600+50+50")
        self.win.resizable(True, True)
        if config.get("overlay", "settings_start_minimized", default=False):
            self.win.iconify()
        else:
            self.win.lift()
            self.win.focus_force()

        # ── Main layout: sidebar (left) + content (right) ──
        main = tk.Frame(self.win, bg=self._bg)
        main.pack(fill=tk.BOTH, expand=True)

        self._tab_bar = tk.Frame(main, bg=self._bg, width=130)
        self._tab_bar.pack(side=tk.LEFT, fill=tk.Y)
        self._tab_bar.pack_propagate(False)

        content_outer = tk.Frame(main, bg=self._bg)
        content_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._scrollbar = tk.Scrollbar(
            content_outer, orient=tk.VERTICAL, troughcolor="#1a1a1a",
            bg="#333333", activebackground="#555555",
            highlightbackground=self._bg, highlightthickness=0,
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            content_outer, bg=self._bg, highlightthickness=0,
            bd=0, yscrollcommand=self._scrollbar.set,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._scrollbar.config(command=self._canvas.yview)

        self._content_frame = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._content_frame, anchor=tk.NW,
        )

        def _on_content_configure(event):
            self._canvas.itemconfig(self._canvas_window, width=event.width)
            self._canvas.config(scrollregion=self._canvas.bbox("all"))

        self._content_frame.bind("<Configure>", _on_content_configure)

        def _on_canvas_configure(event):
            self._canvas.itemconfig(self._canvas_window, width=event.width)

        self._canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._canvas.bind("<MouseWheel>", _on_mousewheel)
        self._content_frame.bind("<MouseWheel>", _on_mousewheel)

        # ── Tab state ──
        self._tabs = {}
        self._active_tab = None

        # ── Build all tabs ──
        self._build_settings_tab()
        self._add_separator()
        self._build_plugins_tab()
        self._add_separator()
        self._build_profiles_tab()
        self._add_separator()
        self._build_api_keys_tab()
        self._add_separator()
        self._build_plugin_settings_tabs()

        # Select first tab
        first_name = next(iter(self._tabs), None)
        if first_name:
            self._select_tab(first_name)

        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Helpers ──

    def _iter_plugins(self):
        """Yield plugin names that have overlay panels (skip settings-only)."""
        if not self._pm:
            return
        for pname in self._pm._name_to_dir:
            inst = self._pm.get_plugin(pname)
            if inst and getattr(inst, "_settings_only", False):
                continue
            yield pname

    def _toggle_all(self, var_dict, toggle_fn, header_var):
        """Generic toggle-all: flip all entries in var_dict via toggle_fn."""
        names = list(var_dict.keys())
        if not names:
            return
        all_on = all(v.get() for v in var_dict.values())
        new_val = not all_on
        for n in names:
            var_dict[n].set(new_val)
            toggle_fn(n, var_dict[n])
        header_var.set(new_val)

    # ── Tab switching ──

    def _select_tab(self, name):
        prev_name, prev_frame = self._active_tab or (None, None)
        if prev_name == name:
            return

        # Update sidebar buttons
        for tname, (btn, _) in self._tabs.items():
            if tname == name:
                btn.config(bg="#1a1a1a", fg=ACCENT, relief=tk.SUNKEN)
            else:
                btn.config(bg=self._bg, fg=self._fg, relief=tk.FLAT)

        # Swap content
        if prev_frame is not None:
            prev_frame.pack_forget()

        _, frame = self._tabs[name]
        frame.pack(fill=tk.BOTH, expand=True, padx=(0, 0))

        self._active_tab = (name, frame)
        self._canvas.yview_moveto(0)

    def _add_tab(self, name, content_frame):
        btn = tk.Button(
            self._tab_bar, text=name, font=self._font,
            bg=self._bg, fg=self._fg, activebackground="#1a1a1a",
            activeforeground=ACCENT, relief=tk.FLAT, anchor=tk.W,
            padx=10, pady=4, bd=0,
            command=lambda n=name: self._select_tab(n),
        )
        btn.pack(fill=tk.X, padx=6, pady=1)
        self._tabs[name] = (btn, content_frame)

    def _add_separator(self):
        tk.Frame(self._tab_bar, bg="#333333", height=1).pack(
            fill=tk.X, padx=10, pady=4,
        )

    # ── Settings tab ──

    def _build_settings_tab(self):
        f = tk.Frame(self._content_frame, bg=self._bg)

        tk.Label(
            f, text="Settings", font=self._font,
            bg=self._bg, fg=ACCENT,
        ).pack(padx=12, pady=(12, 0), anchor=tk.W)

        self._hide_var = tk.BooleanVar(
            value=self._config.get("overlay", "hide_on_unfocus", default=True)
        )
        tk.Checkbutton(
            f, text="Auto-hide when game loses focus",
            variable=self._hide_var,
            bg=self._bg, fg=self._fg, selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            font=self._font, anchor=tk.W,
            command=self._toggle_hide_on_unfocus,
        ).pack(fill=tk.X, padx=12, pady=(12, 0))

        self._hide_console_var = tk.BooleanVar(
            value=self._config.get("overlay", "hide_console", default=False)
        )
        tk.Checkbutton(
            f, text="Hide terminal",
            variable=self._hide_console_var,
            bg=self._bg, fg=self._fg, selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            font=self._font, anchor=tk.W,
            command=self._toggle_console,
        ).pack(fill=tk.X, padx=12, pady=(6, 0))

        self._minimize_var = tk.BooleanVar(
            value=self._config.get("overlay", "settings_start_minimized", default=False)
        )
        tk.Checkbutton(
            f, text="Start settings window minimized",
            variable=self._minimize_var,
            bg=self._bg, fg=self._fg, selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            font=self._font, anchor=tk.W,
            command=self._toggle_start_minimized,
        ).pack(fill=tk.X, padx=12, pady=(6, 0))

        op_frame = tk.Frame(f, bg=self._bg)
        op_frame.pack(fill=tk.X, padx=12, pady=(14, 0))
        tk.Label(
            op_frame, text="Opacity", font=self._font,
            bg=self._bg, fg=self._fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        self._opacity_var = tk.DoubleVar(
            value=self._config.get("overlay", "opacity", default=1.0)
        )
        tk.Scale(
            op_frame, from_=0.05, to=1.0, resolution=0.05,
            orient=tk.HORIZONTAL, variable=self._opacity_var,
            bg=self._bg, fg=self._fg, troughcolor="#1a1a1a",
            activebackground=ACCENT, highlightbackground=self._bg,
            font=self._font, length=200,
            command=self._on_opacity_change,
        ).pack(side=tk.RIGHT)

        fn_frame = tk.Frame(f, bg=self._bg)
        fn_frame.pack(fill=tk.X, padx=12, pady=(14, 0))
        tk.Label(
            fn_frame, text="Font", font=self._font,
            bg=self._bg, fg=self._fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        all_fonts = sorted(tkfont.families())
        current_font = self._config.get("overlay", "font_family", default="Consolas")
        self._font_var = tk.StringVar(value=current_font)
        font_box = ttk.Combobox(
            fn_frame, textvariable=self._font_var,
            values=all_fonts, state="readonly",
            font=("Consolas", 10), width=28,
        )
        font_box.pack(side=tk.RIGHT)
        font_box.bind("<<ComboboxSelected>>", self._on_font_change)

        fs_frame = tk.Frame(f, bg=self._bg)
        fs_frame.pack(fill=tk.X, padx=12, pady=(6, 0))
        tk.Label(
            fs_frame, text="Font Size", font=self._font,
            bg=self._bg, fg=self._fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        current_size = self._config.get("overlay", "font_size", default=11)
        self._font_size_var = tk.IntVar(value=current_size)
        size_box = ttk.Combobox(
            fs_frame, textvariable=self._font_size_var,
            values=list(range(8, 25)), state="readonly",
            font=("Consolas", 10), width=8,
        )
        size_box.pack(side=tk.RIGHT)
        size_box.bind("<<ComboboxSelected>>", self._on_font_size_change)

        tk.Frame(f, bg="#333333", height=1).pack(fill=tk.X, padx=12, pady=(20, 10))

        btn_row = tk.Frame(f, bg=self._bg)
        btn_row.pack(fill=tk.X, padx=12, pady=(0, 12))
        tk.Button(
            btn_row, text="Load All Journals",
            font=self._font,
            bg="#2a2a2a", fg=self._fg,
            activebackground="#3a3a3a", activeforeground="#ffffff",
            relief=tk.FLAT, padx=12, pady=4,
            cursor="hand2",
            command=self._load_all_journals,
        ).pack(side=tk.RIGHT)

        self._add_tab("Settings", f)

    # ── Plugins tab ──

    def _build_plugins_tab(self):
        f = tk.Frame(self._content_frame, bg=self._bg)

        container = tk.Frame(f, bg=self._bg)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 4))

        self._checkboxes = {}
        self._vars = {}
        self._dynamic_cbs = {}
        self._dynamic_vars = {}
        self._lock_cbs = {}
        self._lock_vars = {}
        self._pos_cells = {}
        self._cb_container = container

        sep_color = "#333333"
        hdr_fg = "#777777"

        hdr_frame = tk.Frame(container, bg=self._bg)
        hdr_frame.pack(fill=tk.X, pady=(0, 2))

        hdr_frame.columnconfigure(0, minsize=28)
        hdr_frame.columnconfigure(1, minsize=1)
        hdr_frame.columnconfigure(2, minsize=58)
        hdr_frame.columnconfigure(3, minsize=1)
        hdr_frame.columnconfigure(4, minsize=28)
        hdr_frame.columnconfigure(5, minsize=1)
        hdr_frame.columnconfigure(6, weight=1)
        hdr_frame.columnconfigure(7, minsize=1)
        hdr_frame.columnconfigure(8, minsize=68)

        tk.Label(hdr_frame, text="All", bg=self._bg, fg=hdr_fg,
                 font=("Consolas", 9)).grid(row=0, column=0, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(
            row=0, column=1, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Dynamic", bg=self._bg, fg=hdr_fg,
                 font=("Consolas", 9)).grid(row=0, column=2, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(
            row=0, column=3, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Lock", bg=self._bg, fg=hdr_fg,
                 font=("Consolas", 9)).grid(row=0, column=4, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(
            row=0, column=5, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Plugin", bg=self._bg, fg=hdr_fg,
                 font=("Consolas", 9), anchor=tk.W).grid(
            row=0, column=6, sticky=tk.W)
        tk.Frame(hdr_frame, bg=sep_color, width=1).grid(
            row=0, column=7, rowspan=2, sticky=tk.NS)
        tk.Label(hdr_frame, text="Position", bg=self._bg, fg=hdr_fg,
                 font=("Consolas", 9)).grid(row=0, column=8, sticky=tk.W)

        self._toggle_all_var = tk.BooleanVar()
        self._toggle_all_btn = tk.Checkbutton(
            hdr_frame, text="", variable=self._toggle_all_var,
            bg=self._bg, fg="#e0e0e0", selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            command=self._toggle_all_enabled,
        )
        self._toggle_all_btn.grid(row=1, column=0, sticky=tk.W)

        self._toggle_all_dy_var = tk.BooleanVar()
        self._toggle_all_dy_btn = tk.Checkbutton(
            hdr_frame, text="", variable=self._toggle_all_dy_var,
            bg=self._bg, fg="#e0e0e0", selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            command=self._toggle_all_dynamic,
        )
        self._toggle_all_dy_btn.grid(row=1, column=2, sticky=tk.W)

        self._toggle_all_lock_var = tk.BooleanVar()
        self._toggle_all_lock_btn = tk.Checkbutton(
            hdr_frame, text="", variable=self._toggle_all_lock_var,
            bg=self._bg, fg="#e0e0e0", selectcolor=self._bg,
            activebackground=self._bg, activeforeground="#ffffff",
            command=self._toggle_all_lock,
        )
        self._toggle_all_lock_btn.grid(row=1, column=4, sticky=tk.W)

        self._refresh_plugins()
        self._add_tab("Plugins", f)

    # ── Plugin settings tabs ──

    def _build_plugin_settings_tabs(self):
        if not self._pm:
            return
        for tab_name, plugin_instance in self._pm.get_settings_tabs():
            f = tk.Frame(self._content_frame, bg=self._bg)
            try:
                plugin_instance.build_settings(f, self.overlay, self._config)
            except Exception as e:
                tk.Label(
                    f, text=f"Error loading settings: {e}",
                    font=self._font, bg=self._bg, fg="#ff4444",
                ).pack(pady=20)
            self._add_tab(tab_name, f)

    # ── API Keys tab ──

    def _build_api_keys_tab(self):
        f = tk.Frame(self._content_frame, bg=self._bg)

        self._api_entries = {}
        for key, label in self.API_KEY_FIELDS:
            tk.Label(
                f, text=label, font=self._font,
                bg=self._bg, fg=ACCENT, anchor=tk.W,
            ).pack(fill=tk.X, padx=12, pady=(8, 0))

            val = self._config.get("api_keys", key, default="")
            entry = tk.Entry(
                f, font=self._font, bg="#1a1a1a", fg="#e0e0e0",
                insertbackground="#e0e0e0", relief=tk.FLAT, bd=4,
            )
            entry.insert(0, val)
            entry.pack(fill=tk.X, padx=12, pady=(2, 4))
            self._api_entries[key] = entry

        tk.Label(
            f,
            text="Get your API keys from:\nedsm.net -> My Account -> API Key\ninara.cz -> Community -> API",
            font=self._font_small, bg=self._bg, fg="#666666",
            anchor=tk.W, justify=tk.LEFT,
        ).pack(fill=tk.X, padx=12, pady=(8, 0))

        self._save_status = tk.Label(
            f, text="", font=self._font, bg=self._bg, fg="#44aa44",
        )
        self._save_status.pack(pady=(12, 4))

        tk.Button(
            f, text="Save", font=self._font,
            bg="#2a6e3a", fg="#e0e0e0", relief=tk.FLAT, padx=20, pady=4,
            command=self._save_apis,
        ).pack()

        self._add_tab("API Keys", f)

    # ── Profiles tab ──

    def _build_profiles_tab(self):
        f = tk.Frame(self._content_frame, bg=self._bg)

        tk.Label(
            f, text="Profiles", font=self._font,
            bg=self._bg, fg=ACCENT,
        ).pack(padx=12, pady=(12, 0), anchor=tk.W)

        tk.Label(
            f, text="Save and switch between overlay layouts.",
            font=self._font_small, bg=self._bg, fg="#666666",
        ).pack(padx=12, pady=(4, 0), anchor=tk.W)

        # Profile selector
        sel_frame = tk.Frame(f, bg=self._bg)
        sel_frame.pack(fill=tk.X, padx=12, pady=(14, 0))

        tk.Label(
            sel_frame, text="Active Profile", font=self._font,
            bg=self._bg, fg=self._fg, anchor=tk.W,
        ).pack(side=tk.LEFT)

        profiles = self._get_profile_names()
        active = self._config.get("active_profile", default="")
        if active not in profiles and profiles:
            active = profiles[0]
        self._profile_var = tk.StringVar(value=active)
        self._profile_box = ttk.Combobox(
            sel_frame, textvariable=self._profile_var,
            values=profiles, state="readonly",
            font=("Consolas", 10), width=20,
        )
        self._profile_box.pack(side=tk.RIGHT)
        self._profile_box.bind("<<ComboboxSelected>>", self._on_profile_select)

        # Action buttons
        btn_frame = tk.Frame(f, bg=self._bg)
        btn_frame.pack(fill=tk.X, padx=12, pady=(10, 0))

        tk.Button(
            btn_frame, text="Save", font=self._font,
            bg="#2a6e3a", fg="#e0e0e0", relief=tk.FLAT, padx=10, pady=3,
            command=self._save_profile_as,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="Delete", font=self._font,
            bg="#6e2a2a", fg="#e0e0e0", relief=tk.FLAT, padx=10, pady=3,
            command=self._delete_profile,
        ).pack(side=tk.LEFT, padx=(6, 0))

        tk.Button(
            btn_frame, text="Rename", font=self._font,
            bg="#4a4a2a", fg="#e0e0e0", relief=tk.FLAT, padx=10, pady=3,
            command=self._rename_profile,
        ).pack(side=tk.LEFT, padx=(6, 0))

        self._profile_status = tk.Label(
            f, text="", font=self._font_small, bg=self._bg, fg="#44aa44",
        )
        self._profile_status.pack(padx=12, pady=(8, 0), anchor=tk.W)

        # Profile info
        self._profile_info = tk.Label(
            f, text="", font=self._font_small, bg=self._bg, fg="#666666",
            anchor=tk.W, justify=tk.LEFT,
        )
        self._profile_info.pack(fill=tk.X, padx=12, pady=(10, 0), anchor=tk.W)
        self._refresh_profile_info()

        self._add_tab("Profiles", f)

    def _get_profile_names(self):
        return list(self._config.get("profiles", default={}).keys())

    def _get_active_profile(self):
        return self._config.get("active_profile", default="")

    def _collect_plugin_layout(self):
        """Collect current plugin layout into a dict."""
        layout = {}
        if not self._pm:
            return layout
        for pname in self._iter_plugins():
            pcfg = self._config.plugin_config(pname)
            entry = {}
            for key in ("enabled", "dynamic", "locked", "window_position",
                         "custom_x", "custom_y", "custom_width", "custom_height"):
                if key in pcfg:
                    entry[key] = pcfg[key]
            layout[pname] = entry
        return layout

    def _apply_profile_layout(self, layout):
        """Apply a profile layout to plugins."""
        for pname, data in layout.items():
            pcfg = self._config.data.setdefault("plugins", {}).setdefault(pname, {})
            pcfg.update(data)
            plugin_inst = self._pm.get_plugin(pname) if self._pm else None
            if plugin_inst and hasattr(plugin_inst, "win") and hasattr(plugin_inst.win, "set_locked"):
                plugin_inst.win.set_locked(data.get("locked", False))
            if "window_position" in data and plugin_inst:
                self.overlay.reposition_plugin(pname, data["window_position"])
            if hasattr(plugin_inst, "win") and plugin_inst.win:
                win = plugin_inst.win
                needs_reposition = False
                if "custom_x" in data or "custom_y" in data:
                    win._pl_ox = data.get("custom_x", 0)
                    win._pl_oy = data.get("custom_y", 0)
                    win._custom_pos = bool(win._pl_ox or win._pl_oy)
                    needs_reposition = True
                if "custom_width" in data or "custom_height" in data:
                    win._pl_w = data.get("custom_width", win._pl_w)
                    win._pl_h = data.get("custom_height", win._pl_h)
                    win._custom_size = True
                    needs_reposition = True
                if needs_reposition:
                    self.overlay.resize_plugin(pname)
        self._config.save()
        self._refresh_plugins()

    def _save_profile_as(self):
        name = self._simple_dialog("Save Profile As", "Profile name:")
        if not name:
            return
        if name == "SPECTR":
            self._show_profile_status("Cannot use default profile name", "#ff4444")
            return
        layout = self._collect_plugin_layout()
        self._config.data.setdefault("profiles", {})[name] = layout
        self._config.data["active_profile"] = name
        self._config.save()
        profiles = self._get_profile_names()
        self._profile_box["values"] = profiles
        self._profile_var.set(name)
        self._show_profile_status(f"Created: {name}")
        self._refresh_profile_info()

    def _delete_profile(self):
        name = self._profile_var.get()
        if not name:
            self._show_profile_status("No profile selected", "#ff4444")
            return
        if name == "SPECTR":
            self._show_profile_status("Cannot delete default profile", "#ff4444")
            return
        profiles = self._config.get("profiles", default={})
        if name not in profiles:
            return
        del profiles[name]
        if self._config.get("active_profile") == name:
            remaining = list(profiles.keys())
            new_active = remaining[0] if remaining else ""
            self._config.data["active_profile"] = new_active
            self._profile_var.set(new_active)
        self._config.save()
        self._profile_box["values"] = self._get_profile_names()
        self._show_profile_status(f"Deleted: {name}")
        self._refresh_profile_info()

    def _rename_profile(self):
        old_name = self._profile_var.get()
        if not old_name:
            self._show_profile_status("No profile selected", "#ff4444")
            return
        if old_name == "SPECTR":
            self._show_profile_status("Cannot rename default profile", "#ff4444")
            return
        new_name = self._simple_dialog("Rename Profile", "New name:", prefill=old_name)
        if not new_name or new_name == old_name:
            return
        if new_name == "SPECTR":
            self._show_profile_status("Cannot use default profile name", "#ff4444")
            return
        profiles = self._config.data.setdefault("profiles", {})
        if old_name in profiles:
            profiles[new_name] = profiles.pop(old_name)
        if self._config.get("active_profile") == old_name:
            self._config.data["active_profile"] = new_name
        self._config.save()
        self._profile_var.set(new_name)
        self._profile_box["values"] = self._get_profile_names()
        self._show_profile_status(f"Renamed: {old_name} -> {new_name}")
        self._refresh_profile_info()

    def _on_profile_select(self, event=None):
        name = self._profile_var.get()
        if not name:
            return
        self._config.data["active_profile"] = name
        self._config.save()
        profiles = self._config.get("profiles", default={})
        if name in profiles:
            self._apply_profile_layout(profiles[name])
            self._show_profile_status(f"Loaded: {name}")
        self._refresh_profile_info()

    def _refresh_profile_info(self):
        name = self._profile_var.get()
        profiles = self._config.get("profiles", default={})
        if name in profiles:
            layout = profiles[name]
            if self._pm:
                count = sum(1 for p in layout if p in self._pm._name_to_dir)
            else:
                count = len(layout)
            self._profile_info.config(text=f"Profile '{name}' — {count} plugin(s)")
        else:
            self._profile_info.config(text="No profiles saved yet.")

    def _show_profile_status(self, msg, color="#44aa44"):
        self._profile_status.config(text=msg, fg=color)
        self._clear_status(self._profile_status)

    def _clear_status(self, widget):
        def _do_clear():
            try:
                widget.config(text="")
            except Exception:
                pass
        try:
            self.win.after(2000, _do_clear)
        except Exception:
            pass

    def _simple_dialog(self, title, prompt, prefill=""):
        """Modal dialog that returns a string or None."""
        dlg = tk.Toplevel(self.win)
        dlg.title(title)
        dlg.configure(bg=self._bg)
        dlg.attributes("-topmost", True)
        dlg.transient(self.win)
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.geometry("300x110+100+100")

        tk.Label(
            dlg, text=prompt, font=self._font,
            bg=self._bg, fg=self._fg,
        ).pack(padx=12, pady=(12, 4), anchor=tk.W)

        var = tk.StringVar(value=prefill)
        entry = tk.Entry(
            dlg, textvariable=var, font=self._font,
            bg="#1a1a1a", fg="#e0e0e0", insertbackground="#e0e0e0",
            relief=tk.FLAT, bd=4,
        )
        entry.pack(fill=tk.X, padx=12, pady=(0, 8))
        entry.select_range(0, tk.END)
        entry.focus_force()

        result = [None]

        def on_ok(event=None):
            result[0] = var.get().strip()
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        entry.bind("<Return>", on_ok)
        entry.bind("<Escape>", lambda e: on_cancel())

        btn_frame = tk.Frame(dlg, bg=self._bg)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Button(
            btn_frame, text="OK", font=self._font,
            bg="#2a6e3a", fg="#e0e0e0", relief=tk.FLAT, padx=12, pady=2,
            command=on_ok,
        ).pack(side=tk.RIGHT)
        tk.Button(
            btn_frame, text="Cancel", font=self._font,
            bg="#333333", fg="#e0e0e0", relief=tk.FLAT, padx=12, pady=2,
            command=on_cancel,
        ).pack(side=tk.RIGHT, padx=(0, 6))

        self.win.wait_window(dlg)
        return result[0] if result[0] else None

    # ── Actions ──

    def _save_apis(self):
        api_data = {}
        for key, entry in self._api_entries.items():
            api_data[key] = entry.get().strip()
        self._config.data["api_keys"] = api_data
        self._config.save()
        self._save_status.config(text="Saved!")
        self._clear_status(self._save_status)

    def _on_close(self):
        try:
            geo = self.win.geometry()
            self._config.data.setdefault("overlay", {})["settings_geometry"] = geo
            self._config.save()
        except Exception:
            pass
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

    def _on_font_size_change(self, event=None):
        font_size = self._font_size_var.get()
        self._config.data.setdefault("overlay", {})["font_size"] = font_size
        self._config.save()
        self.overlay._setup_styles()
        self.overlay._reapply_font()

    def _toggle_hide_on_unfocus(self):
        self._config.data.setdefault("overlay", {})["hide_on_unfocus"] = self._hide_var.get()
        self._config.save()

    def _toggle_console(self):
        hide = self._hide_console_var.get()
        self._config.data.setdefault("overlay", {})["hide_console"] = hide
        self._config.save()
        _set_console_visibility(not hide)

    def _toggle_start_minimized(self):
        self._config.data.setdefault("overlay", {})["settings_start_minimized"] = self._minimize_var.get()
        self._config.save()

    def _load_all_journals(self):
        if not self._journal:
            return
        panels = getattr(self.overlay, "_plugin_panels", {})
        hidden = [n for n, p in panels.items() if p._shown]
        for pname in hidden:
            panels[pname].attributes("-alpha", 0.0)
        self._journal.replay_all_journals(
            schedule_fn=self.overlay.schedule,
            done_callback=lambda: self._restore_panels(hidden),
        )

    def _restore_panels(self, hidden):
        panels = getattr(self.overlay, "_plugin_panels", {})
        for pname in hidden:
            p = panels.get(pname)
            if p:
                p.attributes("-alpha", 1.0)

    def _refresh_plugins(self):
        children = self._cb_container.winfo_children()
        # Keep the header frame (first child), destroy everything else
        for w in children[1:]:
            w.destroy()
        self._checkboxes.clear()
        self._vars.clear()
        self._dynamic_cbs.clear()
        self._dynamic_vars.clear()
        self._lock_cbs.clear()
        self._lock_vars.clear()
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
        for pname in self._iter_plugins():
            plugin_cfg = self._config.plugin_config(pname)
            enabled = plugin_cfg.get("enabled", True)
            dynamic = plugin_cfg.get("dynamic", False)
            pos_current = plugin_cfg.get("window_position", "")

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

            locked = plugin_cfg.get("locked", False)
            lock_var = tk.BooleanVar(value=locked)
            lock_cb = tk.Checkbutton(
                row, text="", variable=lock_var,
                bg=self._bg, fg="#e0e0e0", selectcolor="#1a1a1a",
                activebackground=self._bg, activeforeground="#ffffff",
                command=lambda n=pname, v=lock_var: self._toggle_lock(n, v),
            )
            lock_cb.pack(side=tk.LEFT, padx=(4, 0))

            tk.Frame(row, bg=sep_color, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            lbl = tk.Label(
                row, text=pname, bg=self._bg, fg="#e0e0e0",
                font=("Consolas", 11), anchor=tk.W,
            )
            lbl.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)

            tk.Frame(row, bg=sep_color, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            pos_frame = tk.Frame(row, bg=self._bg)
            pos_frame.pack(side=tk.LEFT, padx=(4, 0))

            cells = {}
            for i, pos in enumerate(pos_grid_names):
                r, c = divmod(i, 3)
                is_sel = pos == pos_current
                cell = tk.Label(
                    pos_frame, text=" ", width=2, bd=1, relief=tk.SOLID,
                    bg=ACCENT if is_sel else "#333333",
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
            self._lock_cbs[pname] = lock_cb
            self._lock_vars[pname] = lock_var
            self._pos_cells[pname] = cells

            reload_btn = tk.Button(
                row, text="R", font=("Consolas", 9),
                bg="#333333", fg="#e0e0e0", relief=tk.FLAT,
                padx=2, pady=0, width=2,
                command=lambda n=pname: self._reload_plugin(n),
            )
            reload_btn.pack(side=tk.LEFT, padx=(4, 0))

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
        self._refresh_plugins()

    def _toggle_dynamic(self, name, var):
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["dynamic"] = var.get()
        self._config.save()

    def _toggle_lock(self, name, var):
        locked = var.get()
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["locked"] = locked
        self._config.save()
        if self._pm:
            plugin_inst = self._pm.get_plugin(name)
            if plugin_inst and hasattr(plugin_inst, "win") and hasattr(plugin_inst.win, "set_locked"):
                plugin_inst.win.set_locked(locked)

    def _toggle_position(self, name, pos):
        cells = self._pos_cells.get(name)
        if not cells:
            return
        for p, cell in cells.items():
            cell.config(bg=ACCENT if p == pos else "#333333")
        self._config.data.setdefault("plugins", {}).setdefault(name, {})["window_position"] = pos
        self._config.save()
        plugin_inst = self._pm.get_plugin(name) if self._pm else None
        if plugin_inst and hasattr(plugin_inst, "win"):
            win = plugin_inst.win
            win._custom_pos = False
            win._pl_ox = 0
            win._pl_oy = 0
            win._custom_size = False
            pcfg = self._config.plugin_config(name)
            pcfg.pop("custom_x", None)
            pcfg.pop("custom_y", None)
            pcfg.pop("custom_width", None)
            pcfg.pop("custom_height", None)
            self._config.save()
        self.overlay.reposition_plugin(name, pos)

    def _reload_plugin(self, name):
        """Unload then reload a plugin without restarting the app."""
        if not self._pm:
            return
        # Unload
        self._pm.unload_plugin(name, self.overlay)
        # Reload
        self._pm.load_plugin(name, self.overlay, self.event_bus,
                             self.overlay.config, self.game, self.status)
        self._refresh_plugins()

    def _toggle_all_enabled(self):
        self._toggle_all(self._vars, self._toggle, self._toggle_all_var)

    def _toggle_all_dynamic(self):
        self._toggle_all(self._dynamic_vars, self._toggle_dynamic, self._toggle_all_dy_var)

    def _toggle_all_lock(self):
        self._toggle_all(self._lock_vars, self._toggle_lock, self._toggle_all_lock_var)
