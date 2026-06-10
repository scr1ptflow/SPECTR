import os
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_THEME = {
    "bg": "#0d0d1a",
    "fg": "#e0e0e0",
    "accent": "#00d4aa",
    "border": "#00d4aa",
    "highlight": "#00ffcc",
    "font_family": "Consolas",
    "font_size": 11,
}


def _signed_int_to_rgba(value):
    unsigned = value & 0xFFFFFFFF
    a = (unsigned >> 24) & 0xFF
    r = (unsigned >> 16) & 0xFF
    g = (unsigned >> 8) & 0xFF
    b = unsigned & 0xFF
    return (r, g, b, a)


def _rgba_to_hex(rgba):
    r, g, b, a = rgba
    return f"#{r:02x}{g:02x}{b:02x}"


def _find_element_value(theme_data, key_str):
    for group in theme_data.get("ui_groups", []):
        for element in group.get("Elements", []):
            if element.get("Key") == key_str:
                return element.get("Value")
    return None


def _parse_font(font_str):
    family = "Consolas"
    size = 11
    if font_str:
        parts = font_str.split("px ", 1)
        if len(parts) == 2:
            try:
                size = int(parts[0])
            except ValueError:
                pass
            family = parts[1].strip()
    return family, size


def detect_edhm_theme():
    userprofile = os.environ.get("USERPROFILE", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")

    candidates = []
    v3_data = os.path.join(localappdata, "EDHM-UI-V3", "resources", "data")
    if os.path.isdir(v3_data):
        candidates.append(v3_data)
    user_data = os.path.join(userprofile, "EDHM_UI")
    if os.path.isdir(user_data):
        candidates.append(user_data)

    if not candidates:
        logger.debug("EDHM-UI not found")
        return None

    result = dict(DEFAULT_THEME)

    for base in candidates:
        settings_path = os.path.join(base, "Settings.json")
        hud_cover = None
        user_data_folder = None

        if os.path.isfile(settings_path):
            try:
                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
                hud_cover = settings.get("HUD_Cover")
                user_data_folder = settings.get("UserDataFolder")
                if user_data_folder and "%USERPROFILE%" in user_data_folder:
                    user_data_folder = user_data_folder.replace(
                        "%USERPROFILE%", userprofile
                    )
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Could not read EDHM settings: {e}")

        if hud_cover:
            hud_path = os.path.join(base, "HUD", f"{hud_cover}.json")
            if not os.path.isfile(hud_path) and user_data_folder:
                hud_path = os.path.join(
                    user_data_folder, "HUD", f"{hud_cover}.json"
                )
            if os.path.isfile(hud_path):
                try:
                    with open(hud_path, encoding="utf-8") as f:
                        hud = json.load(f)
                    colors = hud.get("Colors", {})
                    border = colors.get("BorderColor", "orange")
                    font_color = colors.get("FontColor", "white")
                    font_str = colors.get("Font", "14px Segoe UI")
                    highlight_border = colors.get("HighlightBorder", "orange")

                    family, size = _parse_font(font_str)
                    result["font_family"] = family
                    result["font_size"] = size
                    result["border"] = border if not border.startswith("rgba") else result["border"]
                    result["highlight"] = highlight_border if not highlight_border.startswith("rgba") else result["highlight"]
                    result["fg"] = font_color if font_color != "white" else result["fg"]
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug(f"Could not read HUD cover: {e}")

        theme_ini = None
        for subpath in [
            os.path.join(base, "ODYSS", "EDHM", "EDHM-Ini", "ThemeSettings.json"),
            (
                os.path.join(
                    user_data_folder, "ODYSS", "EDHM", "EDHM-Ini", "ThemeSettings.json"
                )
                if user_data_folder
                else None
            ),
        ]:
            if subpath and os.path.isfile(subpath):
                theme_ini = subpath
                break

        if theme_ini:
            try:
                with open(theme_ini, encoding="utf-8") as f:
                    theme = json.load(f)

                theme_name = theme.get("credits", {}).get("theme")
                if theme_name:
                    result["theme_name"] = theme_name

                main_text_val = _find_element_value(
                    theme, "x77|y77|z77|w77"
                )
                if main_text_val is not None:
                    rgba = _signed_int_to_rgba(main_text_val)
                    hex_color = _rgba_to_hex(rgba)
                    result["accent"] = hex_color
                    result["fg"] = hex_color

                icons_val = _find_element_value(theme, "x53|y53|z53")
                if icons_val is not None:
                    rgba = _signed_int_to_rgba(icons_val)
                    result["highlight"] = _rgba_to_hex(rgba)

                side_lines_val = _find_element_value(
                    theme, "x76|y76|z76"
                )
                if side_lines_val is not None:
                    rgba = _signed_int_to_rgba(side_lines_val)
                    result["border"] = _rgba_to_hex(rgba)

                panel_shadow_val = _find_element_value(
                    theme, "x90|y90|z90"
                )
                if panel_shadow_val is not None:
                    rgba = _signed_int_to_rgba(panel_shadow_val)
                    if rgba[0] > 8 or rgba[1] > 8 or rgba[2] > 8:
                        result["bg"] = _rgba_to_hex(rgba)

                logger.info(
                    f"Detected EDHM theme: {theme_name or 'unknown'}, "
                    f"accent={result['accent']}, fg={result['fg']}"
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Could not read EDHM theme config: {e}")

        if hud_cover:
            break

    return result
