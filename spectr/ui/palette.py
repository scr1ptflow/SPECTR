"""
Elite Dangerous Color Palette — SPECTR Theme Reference
======================================================

Inspired by the iconic Elite Dangerous HUD: bright accents on very dark navy,
with ED orange as the signature, scanner teal, and muted blue-gray neutrals.

Tab/Panel Assignments:
  NEWS         → CYAN    (scanner teal)
  COMMANDER    → ORANGE  (THE iconic ED orange)
  SHIP         → BLUE    (ED ship blue)
  LOCATION     → PURPLE  (location purple)
  SCANNER      → CYAN    (scanner teal)
  MISSIONS     → TEAL    (ED teal)
  ENGINEERING  → GREEN   (friendly/wing green)
  LOG          → PINK    (muted pink)
  LABORATORY   → YELLOW  (ED amber)
  SETTINGS     → GRAY    (neutral blue-gray)
"""

# ─── Accent Colors ──────────────────────────────────────────────
ORANGE  = "#ff6600"   # THE iconic ED orange — primary accent
CYAN    = "#00ccdd"   # Bright scanner teal
BLUE    = "#4488cc"   # Bright ship blue
PURPLE  = "#8855cc"   # Bright purple
TEAL    = "#22aa99"   # Bright teal
YELLOW  = "#ffbb33"   # Bright amber
RED     = "#dd3344"   # Danger / hostile
PINK    = "#cc5577"   # Bright pink
GREEN   = "#33bb66"   # Friendly / wing green

# ─── Neutrals ───────────────────────────────────────────────────
GRAY    = "#445566"   # Blue-gray (inactive, secondary)
GRAY_L  = "#667788"   # Light blue-gray (timestamps, muted text)

# ─── Text ───────────────────────────────────────────────────────
WHITE   = "#dde0e8"   # Slightly cool white (ED panel text)

# ─── Backgrounds (very dark navy, like ED cockpit) ─────────────
DARK    = "#050510"   # Near-black — app background
DARK2   = "#0a0a1a"   # Panel / table background
DARK3   = "#101028"   # Header / section background

# ─── Derived / Inline Values ────────────────────────────────────
PANEL_BG_RGBA    = "rgba(5,5,16,180)"
STATUS_BG_RGBA   = "rgba(5,5,16,200)"
CYAN_BORDER_RGBA = "rgba(0,204,221,40)"
CYAN_SEP_RGBA    = "rgba(0,204,221,30)"
CYAN_HOVER_RGBA  = "rgba(0,204,221,12)"

TABLE_BORDER     = "#0e1420"
TABLE_ITEM_BORDER = "#151a28"
SCROLLBAR_HANDLE = "#101828"
INPUT_BORDER     = "#0e1420"

SEGMENT_EMPTY    = (16, 16, 40)
SEGMENT_RED      = (221, 51, 68)
SEGMENT_YELLOW   = (255, 187, 51)
SEGMENT_GREEN    = (51, 187, 102)
INACTIVE_TEXT    = (70, 80, 100)
