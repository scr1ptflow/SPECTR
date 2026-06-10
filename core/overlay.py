import os
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
import logging


logger = logging.getLogger(__name__)

WM_NCHITTEST = 0x0084
HTTRANSPARENT = -1
GWL_EXSTYLE = -20
GWL_WNDPROC = -4
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020

# Configure ctypes return/arg types for win32 API calls
ctypes.windll.user32.GetWindowLongW.restype = wintypes.LONG
ctypes.windll.user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]

ctypes.windll.user32.SetWindowLongW.restype = wintypes.LONG
ctypes.windll.user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]

if hasattr(ctypes.windll.user32, "GetWindowLongPtrW"):
    ctypes.windll.user32.GetWindowLongPtrW.restype = wintypes.LPARAM
    ctypes.windll.user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]

if hasattr(ctypes.windll.user32, "SetWindowLongPtrW"):
    ctypes.windll.user32.SetWindowLongPtrW.restype = wintypes.LPARAM
    ctypes.windll.user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LPARAM]

ctypes.windll.user32.CallWindowProcW.restype = ctypes.c_long
ctypes.windll.user32.CallWindowProcW.argtypes = [
    WNDPROC, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
]

_DWM_ROUNDED = False

def _enable_rounded_corners(hwnd):
    global _DWM_ROUNDED
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
            ctypes.sizeof(ctypes.c_int)
        )
        _DWM_ROUNDED = True
        logger.debug("DWM rounded corners enabled")
    except Exception as e:
        _DWM_ROUNDED = False
        logger.debug(f"DWM rounded corners not available: {e}")

def _enable_dwm_blur(hwnd):
    try:
        class DWM_BLURBEHIND(ctypes.Structure):
            _fields_ = [
                ("dwFlags", ctypes.c_uint),
                ("fEnable", ctypes.c_bool),
                ("hRgnBlur", ctypes.c_void_p),
                ("fTransitionOnMaximized", ctypes.c_bool),
            ]
        blur = DWM_BLURBEHIND()
        blur.dwFlags = 1
        blur.fEnable = True
        ctypes.windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, ctypes.byref(blur))
        logger.debug("DWM blur behind enabled")
    except Exception as e:
        logger.debug(f"DWM blur behind not available: {e}")

def _set_rounded_region(hwnd, width, height, radius):
    try:
        hrgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, width + 1, height + 1,
                                                       radius, radius)
        if hrgn:
            ctypes.windll.user32.SetWindowRgn(hwnd, hrgn, True)
            return True
    except Exception as e:
        logger.warning(f"Could not set rounded region: {e}")
    return False

class PluginPanel:
    """Wraps a Frame to provide a Toplevel-like API for plugins."""
    def __init__(self, frame, overlay, plugin_name,
                 position="center-top", width=600, height=150):
        self._frame = frame
        self._overlay = overlay
        self._plugin_name = plugin_name
        self.container = frame
        self._shown = True
        self._pl_pos = position
        self._pl_w = width
        self._pl_h = height
        self._pl_ox = 0
        self._pl_oy = 0
        self._place_kwargs = {}

    def attributes(self, key, value=None):
        if key == "-alpha":
            if value is not None:
                if value == 0.0 and self._shown:
                    self._shown = False
                    self._frame.place(x=-10000, y=-10000)
                elif value > 0.0 and not self._shown:
                    self._shown = True
                    self._frame.place(**self._place_kwargs)
            return 1.0 if self._shown else 0.0

    def geometry(self, *args):
        if args:
            geo = args[0]
            if "+" in geo or "-" in geo:
                parts = geo.replace("-", "+-").split("+")
                if len(parts) >= 3:
                    try:
                        x = int(parts[-2])
                        y = int(parts[-1])
                        kw = self._place_kwargs.copy()
                        kw["x"] = x
                        kw["y"] = y
                        self._place_kwargs = kw
                        if self._shown:
                            self._frame.place(**kw)
                    except (ValueError, IndexError):
                        pass
            return
        return f"{self._pl_w}x{self._pl_h}+0+0"

    def destroy(self):
        try:
            self._frame.destroy()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._frame, name)


class Overlay:
    STACK_PRIORITY = {
        "Jump Tracker": 0,
        "Compass": 1,
        "Bio Scanner": 2,
        "Combat Tracker": 10,
        "System Info": 20,
        "Exobiology Tracker": 30,
    }

    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.title("ED Overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#000000")
        self.root.attributes("-transparentcolor", "#000000")
        self.root.attributes("-alpha", config.get("overlay", "opacity", default=1.0))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._scale_factor = max(0.25, min(screen_w / 1920, screen_h / 1080))

        self._setup_styles()

        self._game_attach = config.get("overlay", "attach", default=None)
        ox = config.get("overlay", "offset_x", default=0)
        oy = config.get("overlay", "offset_y", default=0)
        self._base_ox = ox
        self._base_oy = oy

        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.update_idletasks()
        root_hwnd = self.root.winfo_id()
        _enable_rounded_corners(root_hwnd)
        if not _DWM_ROUNDED:
            _set_rounded_region(root_hwnd, screen_w, screen_h, radius=12)
        _enable_dwm_blur(root_hwnd)
        self._make_click_through(root_hwnd)
        top_hwnd = ctypes.windll.user32.GetParent(root_hwnd)
        if top_hwnd:
            self._make_click_through(top_hwnd)

        self.root.bind("<Escape>", lambda e: self._on_close())

        if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
            try:
                kernel32 = ctypes.windll.kernel32
                self._ctrl_handler = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint)(
                    lambda ctrl_type: (
                        self.root.after(0, self._on_close),
                        True
                    )[1]
                )
                kernel32.SetConsoleCtrlHandler(self._ctrl_handler, 1)
            except Exception:
                self._ctrl_handler = None

        self._running = True
        self._plugin_containers = {}
        self._plugin_panels = {}
        self._extra_windows = []
        self._game_focused = True
        self._saved_alphas = {}
        self._gui_focus = 0
        self._panel_alphas = {}
        self._position_order = {}


    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        bg = self.config.get("overlay", "bg_color", default="#000000")
        fg = self.config.get("overlay", "fg_color", default="#9ACD32")
        accent = self.config.get("overlay", "accent_color", default="#6B8E23")
        font_family = self.config.get("overlay", "font_family", default="Consolas")
        font_size = self.config.get("overlay", "font_size", default=11)
        self._scaled_font_size = max(8, round(font_size * self._scale_factor))

        style.configure(
            "Overlay.TLabelframe",
            background=bg,
            foreground=accent,
            font=(font_family, self._scaled_font_size),
            relief=tk.FLAT,
            borderwidth=0,
        )
        style.configure(
            "Overlay.TLabelframe.Label",
            background=bg,
            foreground=accent,
            font=(font_family, self._scaled_font_size),
        )
        style.configure("Overlay.TFrame", background=bg)
        style.configure(
            "Overlay.TLabel",
            background=bg,
            foreground=fg,
            font=(font_family, self._scaled_font_size),
        )

    def _reapply_font(self):
        family = self.config.get("overlay", "font_family", default="Consolas")
        size = self._scaled_font_size
        for panel in self._plugin_panels.values():
            self._walk_font(panel._frame, family, size)

    def _walk_font(self, widget, family, size):
        try:
            if isinstance(widget, tk.Label) and not isinstance(widget, ttk.Label):
                cur = widget.cget("font")
                if cur:
                    try:
                        cur_size = cur[1] if isinstance(cur, tuple) else size
                        widget.config(font=(family, cur_size))
                    except Exception:
                        widget.config(font=(family, size))
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._walk_font(child, family, size)
        except Exception:
            pass

    def _screen_pos(self, position, width, height, offset_x=0, offset_y=0):
        sw = self._screen_w
        sh = self._screen_h
        positions = {
            "top-left": (offset_x, offset_y),
            "top": ((sw - width) // 2 + offset_x, offset_y),
            "top-right": (sw - width - offset_x, offset_y),
            "center-left": (offset_x, (sh - height) // 2),
            "center": ((sw - width) // 2 + offset_x, (sh - height) // 2),
            "center-right": (sw - width - offset_x, (sh - height) // 2),
            "bottom-left": (offset_x, sh - height - offset_y),
            "bottom": ((sw - width) // 2 + offset_x, sh - height - offset_y),
            "bottom-right": (sw - width - offset_x, sh - height - offset_y),
        }
        positions["center-top"] = positions["top"]
        positions["center-bottom"] = positions["bottom"]
        positions["bottom-center"] = positions["bottom"]
        return positions.get(position, (sw - width - offset_x, offset_y))

    def _make_click_through(self, hwnd):
        try:
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                0x0020 | 0x0001 | 0x0002 | 0x0004)
            self._hook_nchittest(hwnd)
        except Exception as e:
            logger.warning(f"Could not set click-through: {e}")

    def _hook_nchittest(self, hwnd):
        if not hasattr(self, "_subclass_refs"):
            self._subclass_refs = []

        try:
            get_proc = (
                ctypes.windll.user32.GetWindowLongPtrW
                if hasattr(ctypes.windll.user32, "GetWindowLongPtrW")
                else ctypes.windll.user32.GetWindowLongW
            )
            orig_proc_addr = get_proc(hwnd, GWL_WNDPROC)
            if not orig_proc_addr:
                return
        except Exception:
            return

        orig_proc = ctypes.cast(orig_proc_addr, WNDPROC)

        @WNDPROC
        def wnd_proc(h_wnd, msg, w_param, l_param):
            if msg == WM_NCHITTEST:
                return HTTRANSPARENT
            return ctypes.windll.user32.CallWindowProcW(
                orig_proc, h_wnd, msg, w_param, l_param
            )

        self._subclass_refs.append(wnd_proc)

        try:
            set_proc = (
                ctypes.windll.user32.SetWindowLongPtrW
                if hasattr(ctypes.windll.user32, "SetWindowLongPtrW")
                else ctypes.windll.user32.SetWindowLongW
            )
            set_proc(hwnd, GWL_WNDPROC, wnd_proc)
        except Exception:
            pass

    def create_plugin_container(self, plugin_name, parent=None):
        if parent is not None:
            frame = ttk.LabelFrame(
                parent,
                text=plugin_name,
                style="Overlay.TLabelframe",
                padding=(6, 4),
            )
            frame.pack(fill=tk.X, pady=(0, 6))
        else:
            if not hasattr(self, "_container_anchor"):
                x, y = self._screen_pos("top-left", 320, 310, self._base_ox, self._base_oy)
                self._container_anchor = ttk.Frame(self.root, style="Overlay.TFrame")
                self._container_anchor.place(x=-10000, y=-10000)
                self._anchor_place_kw = {"x": x, "y": y, "width": 320, "height": 310}
            frame = ttk.LabelFrame(
                self._container_anchor,
                text=plugin_name,
                style="Overlay.TLabelframe",
                padding=(6, 4),
            )
            frame.pack(fill=tk.X, pady=(0, 6))
        self._plugin_containers[plugin_name] = frame
        return frame

    def create_plugin_window(self, plugin_name, position="center-top", width=600, height=150, max_height=None):
        self._position_order.setdefault(position, []).append(plugin_name)
        self._position_order[position].sort(key=lambda n: self.STACK_PRIORITY.get(n, 999))
        sf = self._scale_factor
        scaled_w = max(100, round(width * sf))
        scaled_h = max(50, round(height * sf))
        scaled_max_h = round(max_height * sf) if max_height is not None else None
        pad = (max(3, round(6 * sf)), max(2, round(4 * sf)))
        frame = ttk.LabelFrame(
            self.root, text=plugin_name, style="Overlay.TLabelframe",
            padding=pad,
        )
        panel = PluginPanel(frame, self, plugin_name, position, scaled_w, scaled_h)
        panel._scale_factor = sf
        panel._place_kwargs = {"width": scaled_w}
        panel._pl_max_h = scaled_max_h if scaled_max_h is not None else scaled_h
        self._plugin_panels[plugin_name] = panel
        self._extra_windows.append(panel)
        self._restack(position)
        return panel

    def reposition_plugin(self, plugin_name, position):
        panel = self._plugin_panels.get(plugin_name)
        if not panel:
            return
        old_pos = panel._pl_pos
        for pos_list in self._position_order.values():
            if plugin_name in pos_list:
                pos_list.remove(plugin_name)
                break
        self._position_order.setdefault(position, []).append(plugin_name)
        self._position_order[position].sort(key=lambda n: self.STACK_PRIORITY.get(n, 999))
        panel._pl_pos = position
        self._restack(old_pos)
        self._restack(position)

    def _restack(self, position):
        order = self._position_order.get(position)
        if not order:
            return
        gap = max(2, round(4 * self._scale_factor))
        y = None
        for pname in order:
            p = self._plugin_panels.get(pname)
            if not p:
                continue
            x, cur_y = self._screen_pos(position, p._pl_w, p._pl_h, self._base_ox + p._pl_ox, self._base_oy + p._pl_oy)
            if y is None:
                y = cur_y
            kw = {"x": x, "y": y, "width": p._pl_w}
            p._place_kwargs = kw
            if p._shown:
                p._frame.place(**kw)
                p._frame.update_idletasks()
            actual_h = p._frame.winfo_reqheight()
            if p._pl_max_h and actual_h > p._pl_max_h:
                actual_h = p._pl_max_h
                kw["height"] = actual_h
                p._place_kwargs = kw
                if p._shown:
                    p._frame.place(**kw)
            p._pl_h = actual_h
            y += actual_h + gap

    def resize_plugin(self, plugin_name):
        """Recalculate a plugin's auto-height and restack its position."""
        panel = self._plugin_panels.get(plugin_name)
        if panel:
            self._restack(panel._pl_pos)

    def remove_plugin_container(self, plugin_name):
        frame = self._plugin_containers.pop(plugin_name, None)
        if frame:
            try:
                frame.destroy()
            except Exception:
                pass

    def remove_plugin_window(self, plugin_name):
        panel = self._plugin_panels.pop(plugin_name, None)
        if panel:
            for pos_list in self._position_order.values():
                if plugin_name in pos_list:
                    pos_list.remove(plugin_name)
                    break
            try:
                self._extra_windows.remove(panel)
            except ValueError:
                pass
            try:
                panel.destroy()
            except Exception:
                pass

    def schedule(self, ms, callback):
        self.root.after(ms, callback)

    def set_shutdown_hook(self, callback):
        self._shutdown_hook = callback

    def _on_close(self):
        if not getattr(self, "_running", True):
            return
        self._running = False
        try:
            for panel in list(self._extra_windows):
                try:
                    panel.destroy()
                except Exception:
                    pass
            self.root.quit()
            self.root.destroy()
            try:
                self._shutdown_hook()
            except Exception:
                pass
        finally:
            os._exit(0)

    def _hide_on_unfocus(self):
        return self.config.get("overlay", "hide_on_unfocus", default=True)

    def _hide_anchor(self):
        if hasattr(self, "_container_anchor"):
            try:
                self._container_anchor.place(x=-10000, y=-10000)
            except Exception:
                pass

    def _show_anchor(self):
        if hasattr(self, "_container_anchor"):
            try:
                kw = getattr(self, "_anchor_place_kw", None)
                if kw:
                    self._container_anchor.place(**kw)
            except Exception:
                pass

    def set_game_focused(self, focused):
        if focused == self._game_focused:
            return
        self._game_focused = focused
        if not self._hide_on_unfocus():
            for panel in list(self._extra_windows):
                try:
                    panel.attributes("-alpha", 1.0)
                except Exception:
                    pass
            self._saved_alphas.clear()
            self._show_anchor()
            return
        if focused:
            for panel, alpha in list(self._saved_alphas.items()):
                try:
                    panel.attributes("-alpha", alpha)
                except Exception:
                    pass
            self._saved_alphas.clear()
            self._show_anchor()
            if self._gui_focus == 1:
                self.enforce_gui_focus()
        else:
            for panel in list(self._extra_windows):
                try:
                    if self._gui_focus == 1 and panel in self._panel_alphas:
                        self._saved_alphas[panel] = self._panel_alphas[panel]
                    else:
                        self._saved_alphas[panel] = panel.attributes("-alpha")
                    panel.attributes("-alpha", 0.0)
                except Exception:
                    pass
            self._hide_anchor()

    def enforce_game_focus(self):
        if not self._hide_on_unfocus():
            for panel in list(self._extra_windows):
                try:
                    panel.attributes("-alpha", 1.0)
                except Exception:
                    pass
            self._saved_alphas.clear()
            self._show_anchor()
            return
        if self._game_focused:
            return
        for panel in list(self._extra_windows):
            try:
                if panel not in self._saved_alphas:
                    if self._gui_focus == 1 and panel in self._panel_alphas:
                        self._saved_alphas[panel] = self._panel_alphas[panel]
                    else:
                        self._saved_alphas[panel] = panel.attributes("-alpha")
                panel.attributes("-alpha", 0.0)
            except Exception:
                pass
        self._hide_anchor()

    def set_gui_focus(self, gui_focus):
        if gui_focus == self._gui_focus:
            return
        self._gui_focus = gui_focus
        if not self._hide_on_unfocus():
            return
        if gui_focus != 1:
            for panel, alpha in list(self._panel_alphas.items()):
                try:
                    if self._game_focused:
                        panel.attributes("-alpha", alpha)
                except Exception:
                    pass
            self._panel_alphas.clear()
            self._show_anchor()

    def enforce_gui_focus(self):
        if not self._hide_on_unfocus():
            return
        if self._gui_focus != 1:
            return
        for panel in list(self._extra_windows):
            try:
                if panel not in self._panel_alphas:
                    self._panel_alphas[panel] = panel.attributes("-alpha")
                panel.attributes("-alpha", 0.0)
            except Exception:
                pass
        self._hide_anchor()

    def reposition_on_game(self, game_rect):
        if not game_rect:
            return
        gx = game_rect["left"]
        gy = game_rect["top"]
        gw = game_rect["width"]
        gh = game_rect["height"]

        self.root.geometry(f"{gw}x{gh}+{gx}+{gy}")
        self._reposition_panels(gx, gy, gw, gh)
        if hasattr(self, "_container_anchor"):
            w, h = 320, 310
            ox, oy = self._base_ox, self._base_oy
            self._anchor_place_kw = {"x": ox, "y": oy, "width": w, "height": h}
            self._container_anchor.place(**self._anchor_place_kw)

    def _reposition_panels(self, gx, gy, gw, gh):
        bo = self._base_ox
        by = self._base_oy
        for panel in self._extra_windows:
            try:
                pos = panel._pl_pos
                w = panel._pl_w
                h = panel._pl_h  # auto-calculated height
                ox = panel._pl_ox
                oy = panel._pl_oy
                positions = {
                    "top-left": (bo, by),
                    "top-right": (gw - w - bo, by),
                    "bottom-left": (bo, gh - h - by),
                    "bottom-right": (gw - w - bo, gh - h - by),
                    "center-top": ((gw - w) // 2 + bo, by),
                    "center-left": (bo, (gh - h) // 2),
                    "center-bottom": ((gw - w) // 2 + bo, gh - h - by),
                    "center-right": (gw - w - bo, (gh - h) // 2),
                    "bottom-center": ((gw - w) // 2 + bo, gh - h - by),
                }
                x, y = positions.get(pos, (gw - w - bo, by))
                x, y = x + ox, y + oy
                kw = {"x": x, "y": y, "width": w}
                if panel._pl_max_h and h >= panel._pl_max_h:
                    kw["height"] = h
                panel._place_kwargs = kw
                if panel._shown:
                    panel._frame.place(**kw)
            except Exception:
                pass

    def hide_all_extra(self):
        for panel in list(self._extra_windows):
            try:
                panel.attributes("-alpha", 0.0)
            except Exception:
                pass
        self._hide_anchor()

    def show_all_extra(self):
        for panel in list(self._extra_windows):
            try:
                panel.attributes("-alpha", 1.0)
            except Exception:
                pass
        self._show_anchor()
        self.root.update_idletasks()

    def start(self):
        if self._running:
            self.root.mainloop()
