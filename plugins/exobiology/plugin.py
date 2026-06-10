import io
import os
import re
import tkinter as tk
import urllib.request
import urllib.parse
import json
import logging
from core.plugin_base import Plugin
from core.threads import submit as _api_submit
from core.journal import default_journal_path, read_last_journal_event
from .predictor import BioPredictor

logger = logging.getLogger(__name__)


class ExobiologyTracker(Plugin):
    name = "Exobiology Tracker"
    version = "1.0.0"
    description = "Shows predicted bio life forms per body with codex known/new status"

    SIGNAL_KEYS = [
        ("$SAA_SignalType_Biological;", "bio", "Bio"),
        ("$SAA_SignalType_Geological;", "geo", "Geo"),
        ("$SAA_SignalType_Human;", "human", "Human"),
        ("$SAA_SignalType_Guardian;", "guardian", "Guardian"),
        ("$SAA_SignalType_Thargoid;", "thargoid", "Thargoid"),
    ]

    BIO_BODY_CLASSES = {
        "Rocky body",
        "High metal content body",
        "Metal rich body",
        "Icy body",
    }

    EXO_IMAGES_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets", "exo",
    )

    GENUS_IMAGES = {
        "bacterium": "planetary-object.png",
        "stratum": "planetary-object.png",
        "fumerola": "geology-site.png",
        "aleoida": "organic-structure.png",
        "cactoida": "organic-structure.png",
        "clypeus": "organic-structure.png",
        "concha": "organic-structure.png",
        "electricae": "organic-structure.png",
        "fonticulua": "organic-structure.png",
        "frutexa": "organic-structure.png",
        "fungoida": "organic-structure.png",
        "osseus": "organic-structure.png",
        "recepta": "organic-structure.png",
        "tubus": "organic-structure.png",
        "tussock": "organic-structure.png",
    }

    def _load_genus_images(self, icon_size=18):
        self._genus_icons = {}
        try:
            from PIL import Image
        except ImportError:
            logger.debug("PIL not available, skipping genus icons")
            return
        loaded = {}
        for genus, filename in self.GENUS_IMAGES.items():
            if filename not in loaded:
                path = os.path.join(self.EXO_IMAGES_DIR, filename)
                if os.path.exists(path):
                    try:
                        pil_img = Image.open(path)
                        pil_img.thumbnail((icon_size, icon_size), Image.LANCZOS)
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        img = tk.PhotoImage(data=buf.getvalue())
                        loaded[filename] = img
                    except Exception:
                        continue
            self._genus_icons[genus] = loaded.get(filename)

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event
        self.pcfg = config.plugin_config(self.name)
        sf = self.overlay._scale_factor
        win_pos = self.pcfg.get("window_position", "center-left")
        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=240, height=250, max_height=250
        )
        self.win._pl_ox = round(-5 * sf)
        self.win.update_idletasks()
        parent = self.win.container
        self.win.attributes("-alpha", 1.0)

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        fg = config.get("overlay", "fg_color", default="#9ACD32")
        accent = config.get("overlay", "accent_color", default="#6B8E23")

        self.current_system = "--"
        self.bodies = {}
        self.predictor = BioPredictor()
        self._known_genuses = set()
        self._update_pending = False
        self._load_genus_images(icon_size=max(8, round(18 * sf)))

        self.system_label = tk.Label(
            parent,
            text="System: --",
            font=(font[0], font[1]),
            bg=bg,
            fg=fg,
            anchor=tk.W,
        )
        self.system_label.pack(fill=tk.X, pady=(0, 2))

        self.display = tk.Text(
            parent,
            font=font,
            bg=bg,
            fg=fg,
            padx=0,
            pady=0,
            highlightthickness=0,
            borderwidth=0,
            state=tk.DISABLED,
            height=2,
        )
        self.display.pack(fill=tk.X)
        self.display.tag_config("bio_known", foreground="#00d4aa")
        self.display.tag_config("bio_new", foreground="#ff6b6b")
        self.display.tag_config("body_line", foreground=accent)

        self._frame_shown = False

        self._journal_dir = default_journal_path(config.get("journal_path"))
        self._restore_state_from_journal()

        event_bus.subscribe("status", self._handler)
        event_bus.subscribe("journal:FSDJump", self._handler)
        event_bus.subscribe("journal:Location", self._handler)
        event_bus.subscribe("journal:Scan", self._handler)
        event_bus.subscribe("journal:FSSBodySignals", self._handler)
        event_bus.subscribe("journal:SAAScanComplete", self._handler)
        event_bus.subscribe("journal:CodexEntry", self._handler)

    def on_unload(self):
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass
        self.event_bus.unsubscribe("status", self._handler)
        self.event_bus.unsubscribe("journal:FSDJump", self._handler)
        self.event_bus.unsubscribe("journal:Location", self._handler)
        self.event_bus.unsubscribe("journal:Scan", self._handler)
        self.event_bus.unsubscribe("journal:FSSBodySignals", self._handler)
        self.event_bus.unsubscribe("journal:SAAScanComplete", self._handler)
        self.event_bus.unsubscribe("journal:CodexEntry", self._handler)

    def _is_bio_candidate(self, planet_class):
        return planet_class.lower() in {c.lower() for c in self.BIO_BODY_CLASSES}

    def _parse_signals(self, signals_list):
        counts = {}
        for sig in signals_list:
            sig_type = sig.get("Type", "")
            count = sig.get("Count", 0)
            matched = False
            for pattern, short_key, _ in self.SIGNAL_KEYS:
                if pattern in sig_type:
                    counts[short_key] = counts.get(short_key, 0) + count
                    matched = True
                    break
            if not matched:
                counts["other"] = counts.get("other", 0) + count
        return counts

    def _extract_body_data(self, scan_data):
        planet_class = scan_data.get("PlanetClass", "")
        if not self._is_bio_candidate(planet_class):
            return None
        return {
            "planet_class": planet_class,
            "temperature": scan_data.get("SurfaceTemperature"),
            "atmosphere": scan_data.get("AtmosphereType", ""),
            "gravity": scan_data.get("SurfaceGravity"),
            "volcanism": scan_data.get("Volcanism", ""),
        }

    def _seed_from_cache(self):
        if not self.game or self.current_system == "--":
            return
        prefix = self.current_system + " "
        for bname, bdata in self.game.body_data_cache.items():
            if not bname.startswith(prefix):
                continue
            pclass = bdata.get("planet_class", "")
            if self._is_bio_candidate(pclass):
                self.bodies[bname] = {"body_data": dict(bdata)}

    def _fetch_edsm_bodies(self):
        system = self.current_system
        if not system or system == "--":
            return
        try:
            url = "https://www.edsm.net/api-system-v1/bodies?" + urllib.parse.urlencode({
                "systemName": system
            })
            req = urllib.request.Request(url, headers={"User-Agent": "SPECTR/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug(f"EDSM body fetch failed for {system}: {e}")
            return

        if self.current_system != system:
            return

        bodies = data.get("bodies", [])
        new_bodies = {}
        for b in bodies:
            if b.get("type") != "Planet":
                continue
            body_name = b.get("name", "")
            pclass = b.get("subType", "")
            if not body_name or not pclass:
                continue
            if not self._is_bio_candidate(pclass):
                continue
            bdata = {"planet_class": pclass}
            t = b.get("temperature")
            if t is not None:
                bdata["temperature"] = t
            atm = b.get("atmosphereType", "")
            if atm:
                bdata["atmosphere"] = atm
            g = b.get("gravity")
            if g is not None:
                bdata["gravity"] = g
            v = b.get("volcanismType", "")
            if v:
                bdata["volcanism"] = v
            new_bodies[body_name] = {"body_data": bdata}

        if new_bodies:
            self.overlay.schedule(0, lambda s=system, nb=new_bodies: self._apply_edsm_bodies(s, nb))

    def _apply_edsm_bodies(self, system, new_bodies):
        if self.current_system != system:
            return
        for body_name, body_data in new_bodies.items():
            if body_name not in self.bodies:
                self.bodies[body_name] = body_data
        self._update_display()

    def _deferred_update(self):
        self._update_pending = False
        self._update_display()

    def _schedule_update(self):
        if self._update_pending:
            return
        self._update_pending = True
        self.overlay.schedule(80, self._deferred_update)

    def _run_prediction(self, body_name):
        body = self.bodies.get(body_name)
        if not body:
            return []
        body_data = body.get("body_data")
        if not body_data:
            return []
        return self.predictor.predict(body_data)

    def _restore_state_from_journal(self):
        entry = read_last_journal_event(self._journal_dir, ("Location", "FSDJump"))
        if entry:
            self.current_system = entry.get("StarSystem", entry.get("System", "--"))
            self._update_pending = False
            self.bodies = {}
            self._seed_from_cache()
            self._update_display()
            if self.current_system != "--":
                _api_submit(self._fetch_edsm_bodies)

    def on_event(self, event, data):
        if event == "status":
            in_fss = self.status.is_in_fss() if self.status else False
            has_data = bool(self.bodies)
            dynamic = self.pcfg.get("dynamic", False)
            if dynamic:
                visible = in_fss or has_data
                if visible != self._frame_shown:
                    self._frame_shown = visible
                    self.win.attributes("-alpha", 1.0 if visible else 0.0)
            else:
                self._frame_shown = True
                self.win.attributes("-alpha", 1.0)
            return

        if event == "journal:CodexEntry":
            name = data.get("Name", "")
            if name.startswith("$Codex_Ent_"):
                inner = name[len("$Codex_Ent_"):].rstrip(";")
                genus = inner.split("_")[0].lower()
                if genus:
                    self._known_genuses.add(genus)
            return

        if event in ("journal:FSDJump", "journal:Location"):
            self.current_system = data.get("StarSystem", data.get("System", "--"))
            self._update_pending = False
            self.bodies = {}
            self._seed_from_cache()
            self._update_display()
            _api_submit(self._fetch_edsm_bodies)
            return

        body_name = data.get("BodyName", "")
        if not body_name:
            return

        if event == "journal:Scan":
            body_data = self._extract_body_data(data)
            if body_name in self.bodies:
                if body_data is not None:
                    self.bodies[body_name].setdefault("body_data", {}).update(body_data)
            else:
                entry = {}
                if body_data is not None:
                    entry["body_data"] = body_data
                self.bodies[body_name] = entry
            signals = data.get("Signals")
            if signals:
                counts = self._parse_signals(signals)
                existing = self.bodies[body_name]
                for k, v in counts.items():
                    existing[k] = max(existing.get(k, 0), v)
            self._schedule_update()
            return

        signals = data.get("Signals")
        if not signals:
            return

        counts = self._parse_signals(signals)
        confirmed = event == "journal:SAAScanComplete"

        if body_name in self.bodies:
            existing = self.bodies[body_name]
            for k, v in counts.items():
                existing[k] = max(existing.get(k, 0), v)
            if confirmed:
                existing["confirmed"] = True
        else:
            counts["confirmed"] = confirmed
            self.bodies[body_name] = counts

        self._schedule_update()

    def _update_display(self):
        self.system_label.config(text=f"System: {self.current_system}")

        self.display.config(state=tk.NORMAL)
        self.display.delete("1.0", tk.END)

        if not self.bodies:
            self.display.insert(tk.END, "Use FSS to discover signals")
            self.display.config(state=tk.DISABLED, height=2)
            self.overlay.resize_plugin(self.name)
            return

        total_value = 0
        lines_added = False
        first_body = True

        for body, info in sorted(self.bodies.items()):
            predictions = self._run_prediction(body)
            if not predictions:
                continue
            lines_added = True

            if body.lower().startswith(self.current_system.lower()):
                body_short = body[len(self.current_system):].strip()
            else:
                body_short = body
            body_short = re.sub(r"(\d+) ([a-z])", lambda m: m.group(1) + m.group(2).upper(), body_short)

            if not first_body:
                self.display.insert(tk.END, "\n")
            first_body = False

            self.display.insert(tk.END, f"Body {body_short}\n", "body_line")

            for pred in predictions:
                genus = pred["genus"]
                reward = pred["reward_max"]
                known = genus.lower() in self._known_genuses
                tag = "bio_known" if known else "bio_new"
                icon = self._genus_icons.get(genus.lower())
                if icon:
                    self.display.image_create(tk.END, image=icon)
                    self.display.insert(tk.END, " ")
                else:
                    self.display.insert(tk.END, " - ")
                self.display.insert(tk.END, f"{genus} ({reward:,} CR)\n", tag)
                total_value += reward

        if not lines_added:
            self.display.insert(tk.END, "No life forms predicted")

        if total_value > 0:
            self.display.insert(tk.END, f"\nPotential value: {total_value:,} CR")

        visual_lines = int(self.display.count("1.0", "end-1c", "displaylines")[0])
        self.display.config(state=tk.DISABLED, height=visual_lines)

        self.overlay.resize_plugin(self.name)

        has_data = bool(self.bodies)
        in_fss = self.status.is_in_fss() if self.status else False
        dynamic = self.pcfg.get("dynamic", False)
        if dynamic:
            visible = in_fss or has_data
            if visible != self._frame_shown:
                self._frame_shown = visible
                self.win.attributes("-alpha", 1.0 if visible else 0.0)
        else:
            self._frame_shown = True
            self.win.attributes("-alpha", 1.0)
