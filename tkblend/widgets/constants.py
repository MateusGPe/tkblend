"""
Constants for tkblend vector widgets.

Contains design tokens, standard dimensions, animation durations,
focus ring metrics, typography baseline factors, and default widget properties.
"""

from __future__ import annotations

# ==============================================================================
# Global & Shared Design Constants
# ==============================================================================

# Scaling baseline ratio (Tk standard 72 DPI base -> 96 / 72 = 4/3)
TK_SCALING_BASE: float = 1.3333333333333333
TK_SCALING_MIN_THRESHOLD: float = 0.1

# Standard typography alignment factors
TEXT_BASELINE_OFFSET_RATIO: float = 0.35
ICON_BASELINE_OFFSET_RATIO: float = 0.35
DEFAULT_FONT_SIZE: float = 13.0
ICON_FONT_SIZE_RATIO: float = 1.1
ICON_STANDALONE_SIZE_RATIO: float = 0.55

# Standard focus ring metrics
FOCUS_RING_WIDTH: float = 2.0
FOCUS_RING_PADDING: float = 1.5
FOCUS_RING_ROUND_OFFSET: float = 2.0
COLOR_TRANSPARENT: str = "#00000000"

# Standard Cursors
CURSOR_HAND: str = "hand2"
CURSOR_IBEAM: str = "xterm"
CURSOR_DEFAULT: str = ""

# Standard Widget States
STATE_NORMAL: str = "normal"
STATE_DISABLED: str = "disabled"

# Standard Icon Families
DEFAULT_ICON_FAMILY: str = "fa-solid"

# Standard Fallback Colors
FALLBACK_THUMB_COLOR: str = "#ffffff"
FALLBACK_THUMB_BORDER_COLOR: str = "#00000022"
FALLBACK_DARK_BG: str = "#100e14"
FALLBACK_LIGHT_BG: str = "#ffffff"

# ==============================================================================
# Base Control Constants
# ==============================================================================

DEFAULT_BASE_WIDTH: int = 100
DEFAULT_BASE_HEIGHT: int = 30

# ==============================================================================
# Button Constants
# ==============================================================================

DEFAULT_BUTTON_TEXT: str = "Button"
DEFAULT_BUTTON_WIDTH: int = 120
DEFAULT_BUTTON_HEIGHT: int = 36
DEFAULT_BUTTON_CORNER_RADIUS: float = 8.0
DEFAULT_BUTTON_BORDER_WIDTH: float = 0.0
DEFAULT_BUTTON_SHADOW_BLUR: float = 6.0
DEFAULT_BUTTON_SHADOW_OFFSET_Y: float = 2.0
DEFAULT_BUTTON_ICON_TEXT_SPACING: float = 8.0

# Button Animation Durations (ms)
BUTTON_ANIM_HOVER_MS: int = 120
BUTTON_ANIM_PRESS_MS: int = 60
BUTTON_ANIM_KEY_PRESS_MS: int = 40
BUTTON_ANIM_KEY_RELEASE_MS: int = 80

# Button Press Visual Dynamics
BUTTON_PRESS_DISPLACEMENT_Y: float = 1.5
BUTTON_PRESS_SHADOW_BLUR_SCALE: float = 0.5
BUTTON_PRESS_SHADOW_OFFSET_SCALE: float = 0.4

# ==============================================================================
# CheckBox Constants
# ==============================================================================

DEFAULT_CHECKBOX_WIDTH: int = 140
DEFAULT_CHECKBOX_HEIGHT: int = 24
DEFAULT_CHECKBOX_BOX_SIZE: int = 20
DEFAULT_CHECKBOX_CORNER_RADIUS: float = 5.0
DEFAULT_CHECKBOX_BORDER_WIDTH: float = 1.5
DEFAULT_CHECKBOX_STROKE_WIDTH: float = 2.2
DEFAULT_CHECKBOX_LEFT_MARGIN: float = 2.0
DEFAULT_CHECKBOX_TEXT_SPACING: float = 10.0
DEFAULT_CHECKBOX_COMPACT_EXTRA_PAD: int = 6

CHECKBOX_ANIM_DURATION_MS: int = 140

# Checkmark Vector Path Proportions (relative to box size)
CHECKMARK_P1: tuple[float, float] = (0.22, 0.52)
CHECKMARK_P2: tuple[float, float] = (0.42, 0.72)
CHECKMARK_P3: tuple[float, float] = (0.78, 0.28)
CHECKMARK_SPLIT_THRESHOLD: float = 0.4

# ==============================================================================
# Switch / Toggle Constants
# ==============================================================================

DEFAULT_SWITCH_WIDTH: int = 140
DEFAULT_SWITCH_HEIGHT: int = 28
DEFAULT_SWITCH_TRACK_WIDTH: int = 44
DEFAULT_SWITCH_TRACK_HEIGHT: int = 24
DEFAULT_SWITCH_LEFT_MARGIN: float = 2.0
DEFAULT_SWITCH_TEXT_SPACING: float = 10.0
DEFAULT_SWITCH_COMPACT_EXTRA_PAD: int = 6

SWITCH_ANIM_DURATION_MS: int = 160

# ==============================================================================
# Slider Constants
# ==============================================================================

DEFAULT_SLIDER_WIDTH: int = 200
DEFAULT_SLIDER_HEIGHT: int = 24
DEFAULT_SLIDER_FROM: float = 0.0
DEFAULT_SLIDER_TO: float = 100.0
DEFAULT_SLIDER_VALUE: float = 0.0
DEFAULT_SLIDER_THUMB_RADIUS: float = 8.0
DEFAULT_SLIDER_TRACK_THICKNESS: float = 4.0
DEFAULT_SLIDER_ORIENTATION: str = "horizontal"

SLIDER_TRACK_PADDING_EXTRA: float = 2.0
SLIDER_KEY_STEP_RATIO: float = 0.05
SLIDER_VERTICAL_SHADOW_OFFSET_Y: float = 1.0
SLIDER_VERTICAL_SHADOW_BLUR: float = 3.0
SLIDER_VERTICAL_SHADOW_COLOR: str = "#00000040"
SLIDER_VERTICAL_BORDER_WIDTH: float = 1.5
SLIDER_VERTICAL_FOCUS_RING_OFFSET: float = 2.0

# ==============================================================================
# RadioButton Constants
# ==============================================================================

DEFAULT_RADIO_WIDTH: int = 140
DEFAULT_RADIO_HEIGHT: int = 24
DEFAULT_RADIO_SIZE: int = 20
DEFAULT_RADIO_BORDER_WIDTH: float = 1.5
DEFAULT_RADIO_LEFT_MARGIN: float = 2.0
DEFAULT_RADIO_TEXT_SPACING: float = 10.0
DEFAULT_RADIO_COMPACT_EXTRA_PAD: int = 6

RADIO_ANIM_DURATION_MS: int = 140
RADIO_INNER_DOT_RATIO: float = 0.45
RADIO_FOCUS_RING_OFFSET: float = 2.0

# ==============================================================================
# ProgressBar Constants
# ==============================================================================

DEFAULT_PROGRESS_WIDTH: int = 200
DEFAULT_PROGRESS_HEIGHT: int = 8
DEFAULT_PROGRESS_DETERMINATE_SPEED: float = 1.0
DEFAULT_PROGRESS_INDETERMINATE_SPEED: float = 1.0
DEFAULT_PROGRESS_BORDER_WIDTH: float = 0.0
DEFAULT_PROGRESS_STEP_AMOUNT: float = 0.01

PROGRESS_ANIM_INTERVAL_MS: int = 16
PROGRESS_INDETERMINATE_PHASE_STEP: float = 0.015
PROGRESS_DETERMINATE_AUTO_STEP: float = 0.005

# ==============================================================================
# Card Constants
# ==============================================================================

DEFAULT_CARD_WIDTH: int = 240
DEFAULT_CARD_HEIGHT: int = 160
DEFAULT_CARD_CORNER_RADIUS: float = 12.0
DEFAULT_CARD_BORDER_WIDTH: float = 1.0
DEFAULT_CARD_SHADOW_BLUR: float = 10.0
DEFAULT_CARD_SHADOW_SPREAD: float = 0.0
DEFAULT_CARD_SHADOW_OFFSET_X: float = 0.0
DEFAULT_CARD_SHADOW_OFFSET_Y: float = 3.0

# ==============================================================================
# Label Constants
# ==============================================================================

DEFAULT_LABEL_WIDTH: int = 100
DEFAULT_LABEL_HEIGHT: int = 24
DEFAULT_LABEL_CORNER_RADIUS: float = 0.0
DEFAULT_LABEL_BORDER_WIDTH: float = 0.0
DEFAULT_LABEL_ALIGN: str = "left"
DEFAULT_LABEL_ICON_TEXT_SPACING: float = 6.0
DEFAULT_LABEL_SIDE_PADDING: float = 4.0
