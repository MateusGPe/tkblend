"""
tkblend.widgets - Pure Blend2D Vector UI Controls powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.widgets.frame import Frame
from tkblend.widgets.button import Button
from tkblend.widgets.switch import Switch
from tkblend.widgets.slider import Slider
from tkblend.widgets.checkbox import CheckBox
from tkblend.widgets.progressbar import ProgressBar
from tkblend.widgets.circular_progress import CircularProgress, Gauge
from tkblend.widgets.radiobutton import RadioButton
from tkblend.widgets.card import Card
from tkblend.widgets.label import Label
from tkblend.widgets.badge import Badge, Avatar
from tkblend.widgets.segmented_button import SegmentedButton, SegmentedControl
from tkblend.widgets.range_slider import RangeSlider
from tkblend.widgets.combobox import ComboBox, OptionMenu, Dropdown
from tkblend.widgets.textbox import TextBox, Text, Entry, SearchEntry
from tkblend.widgets.scrollable_frame import ScrollableFrame, VectorScrollbar, ScrollBar
from tkblend.widgets.table import Table
from tkblend.widgets.tabview import Tabview, TabView
from tkblend.widgets.sparkline import Sparkline
from tkblend.widgets import constants
from tkblend.widgets import utils

# Aliases
Toggle = Switch
Progress = ProgressBar
Progressbar = ProgressBar

__all__ = [
    "BaseControl",
    "ScalingTracker",
    "Frame",
    "Button",
    "Switch",
    "Toggle",
    "Slider",
    "CheckBox",
    "ProgressBar",
    "Progress",
    "Progressbar",
    "CircularProgress",
    "Gauge",
    "RadioButton",
    "Card",
    "Label",
    "Badge",
    "Avatar",
    "SegmentedButton",
    "SegmentedControl",
    "RangeSlider",
    "ComboBox",
    "OptionMenu",
    "Dropdown",
    "TextBox",
    "Text",
    "Entry",
    "SearchEntry",
    "ScrollableFrame",
    "VectorScrollbar",
    "ScrollBar",
    "Table",
    "Tabview",
    "TabView",
    "Sparkline",
    "constants",
    "utils",
]


