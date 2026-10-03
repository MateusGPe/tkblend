"""
tkblend.widgets - Pure Blend2D Vector UI Controls powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.widgets.button import Button
from tkblend.widgets.switch import Switch
from tkblend.widgets.slider import Slider
from tkblend.widgets.checkbox import CheckBox
from tkblend.widgets.progressbar import ProgressBar
from tkblend.widgets.radiobutton import RadioButton
from tkblend.widgets.card import Card
from tkblend.widgets.label import Label
from tkblend.widgets import constants
from tkblend.widgets import utils

# Aliases
Toggle = Switch
Progress = ProgressBar

__all__ = [
    "BaseControl",
    "ScalingTracker",
    "Button",
    "Switch",
    "Toggle",
    "Slider",
    "CheckBox",
    "ProgressBar",
    "Progress",
    "RadioButton",
    "Card",
    "Label",
    "constants",
    "utils",
]

