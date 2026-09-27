#pragma once

namespace tkblend {

inline const char* DEFAULT_DARK_THEME_CSS = R"css(
/* Dark Theme */
:root {
  --bg: #100e14;
  --fg: #e6e0e9;
  --surface: #1d1b20;
  --surface-border: #36343b;
  --card-bg: #25232a;
  --card-border: #49454f;
  --primary: #d0bcff;
  --primary-hover: #e8def8;
  --primary-active: #b69df8;
  --primary-fg: #381e72;
  --secondary: #4a4458;
  --secondary-hover: #585168;
  --secondary-active: #332d41;
  --secondary-fg: #e8def8;
  --text-muted: #cac4d0;
  --fg-subtle: #cac4d0;
  --shadow: rgba(0, 0, 0, 0.35);
  --shadow-color: rgba(0, 0, 0, 0.35);
  --accent: #efb8c8;
  --success: #85d697;
  --warning: #ffb877;
  --destructive: #ffb4ab;
  --danger: #ffb4ab;
  --input-bg: #1d1b20;
  --input-border: #49454f;
  --input-focus: #d0bcff;
  --track-bg: #36343b;
  --thumb-color: #d0bcff;
}

button {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
  font-size: 13px;
  font-family: sans-serif;
  font-weight: 500;
}
button:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
button:active {
  background: var(--primary-active);
  box-shadow: none;
}
button:disabled {
  background: var(--surface);
  color: var(--text-muted);
  border: 1px solid var(--card-border);
  box-shadow: none;
}

.btn-primary, button.primary {
  background: var(--primary);
  color: var(--primary-fg);
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}
.btn-primary:hover, button.primary:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
.btn-primary:active, button.primary:active {
  background: var(--primary-active);
  box-shadow: none;
}

.btn-secondary, button.secondary {
  background: var(--secondary);
  color: var(--secondary-fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: 0 1px 2px var(--shadow);
}
.btn-secondary:hover, button.secondary:hover {
  background: var(--secondary-hover);
}
.btn-secondary:active, button.secondary:active {
  background: var(--secondary-active);
}

.btn-accent, button.accent, .btn-info, button.info {
  background: var(--accent);
  color: #100e14;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}
.btn-accent:hover, button.accent:hover, .btn-info:hover, button.info:hover {
  background: var(--primary-hover);
}

.btn-destructive, button.destructive, .btn-danger, button.danger {
  background: var(--destructive);
  color: #410002;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-success, button.success {
  background: var(--success);
  color: #003912;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-warning, button.warning {
  background: var(--warning);
  color: #100e14;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-outline, button.outline, .btn-outline-primary {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 8px;
  box-shadow: none;
}
.btn-outline:hover, button.outline:hover, .btn-outline-primary:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
.btn-outline:active, button.outline:active, .btn-outline-primary:active {
  background: var(--primary-active);
}

.btn-outline-secondary {
  background: transparent;
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
}
.btn-outline-danger, .btn-outline-destructive {
  background: transparent;
  color: var(--destructive);
  border: 1px solid var(--destructive);
  border-radius: 8px;
}
.btn-outline-success {
  background: transparent;
  color: var(--success);
  border: 1px solid var(--success);
  border-radius: 8px;
}

card, .card {
  background: var(--card-bg);
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow);
}

input, entry, .input, .entry {
  background: var(--input-bg);
  color: var(--fg);
  border: 1px solid var(--input-border);
  border-radius: 6px;
  font-size: 13px;
}
input:focus, entry:focus {
  border: 1.5px solid var(--input-focus);
}

badge, .badge {
  background: var(--secondary);
  color: var(--fg);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.badge-primary, badge.primary {
  background: var(--primary);
  color: var(--primary-fg);
}
.badge-success, badge.success {
  background: var(--success);
  color: #100e14;
}
.badge-warning, badge.warning {
  background: var(--warning);
  color: #100e14;
}
.badge-danger, .badge-destructive, badge.danger {
  background: var(--destructive);
  color: #100e14;
}

switch, .switch {
  background: var(--track-bg);
  color: var(--thumb-color);
  border-radius: 12px;
}
switch:checked {
  background: var(--primary);
}

progress, .progress {
  background: var(--track-bg);
  color: var(--primary);
  border-radius: 6px;
}

slider, .slider {
  background: var(--track-bg);
  color: var(--primary);
  border-radius: 4px;
}
)css";

inline const char* DEFAULT_LIGHT_THEME_CSS = R"css(
/* Light Theme */
:root {
  --bg: #f4f5f7;
  --fg: #0f172a;
  --surface: #e2e8f0;
  --surface-border: #cbd5e1;
  --card-bg: #ffffff;
  --card-border: #cbd5e1;
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --primary-active: #4338ca;
  --primary-fg: #ffffff;
  --secondary: #e2e8f0;
  --secondary-hover: #cbd5e1;
  --secondary-active: #94a3b8;
  --secondary-fg: #0f172a;
  --text-muted: #475569;
  --fg-subtle: #475569;
  --shadow: rgba(0, 0, 0, 0.12);
  --shadow-color: rgba(0, 0, 0, 0.12);
  --accent: #0ea5e9;
  --success: #10b981;
  --warning: #f59e0b;
  --destructive: #ef4444;
  --danger: #ef4444;
  --input-bg: #ffffff;
  --input-border: #94a3b8;
  --input-focus: #6366f1;
  --track-bg: #e2e8f0;
  --thumb-color: #6366f1;
}

button {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: 0 1px 3px var(--shadow);
  font-size: 13px;
  font-family: sans-serif;
  font-weight: 500;
}
button:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
button:active {
  background: var(--primary-active);
  box-shadow: none;
}
button:disabled {
  background: var(--surface);
  color: var(--text-muted);
  border: 1px solid var(--card-border);
  box-shadow: none;
}

.btn-primary, button.primary {
  background: var(--primary);
  color: var(--primary-fg);
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}
.btn-primary:hover, button.primary:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
.btn-primary:active, button.primary:active {
  background: var(--primary-active);
  box-shadow: none;
}

.btn-secondary, button.secondary {
  background: var(--secondary);
  color: var(--secondary-fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
}
.btn-secondary:hover, button.secondary:hover {
  background: var(--secondary-hover);
}
.btn-secondary:active, button.secondary:active {
  background: var(--secondary-active);
}

.btn-accent, button.accent, .btn-info, button.info {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}
.btn-accent:hover, button.accent:hover, .btn-info:hover, button.info:hover {
  background: var(--primary-hover);
}

.btn-destructive, button.destructive, .btn-danger, button.danger {
  background: var(--destructive);
  color: #ffffff;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-success, button.success {
  background: var(--success);
  color: #ffffff;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-warning, button.warning {
  background: var(--warning);
  color: #ffffff;
  border: 1px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.btn-outline, button.outline, .btn-outline-primary {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 8px;
  box-shadow: none;
}
.btn-outline:hover, button.outline:hover, .btn-outline-primary:hover {
  background: var(--primary-hover);
  color: var(--primary-fg);
}
.btn-outline:active, button.outline:active, .btn-outline-primary:active {
  background: var(--primary-active);
}

.btn-outline-secondary {
  background: transparent;
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
}
.btn-outline-danger, .btn-outline-destructive {
  background: transparent;
  color: var(--destructive);
  border: 1px solid var(--destructive);
  border-radius: 8px;
}
.btn-outline-success {
  background: transparent;
  color: var(--success);
  border: 1px solid var(--success);
  border-radius: 8px;
}

card, .card {
  background: var(--card-bg);
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow);
}

input, entry, .input, .entry {
  background: var(--input-bg);
  color: var(--fg);
  border: 1px solid var(--input-border);
  border-radius: 6px;
  font-size: 13px;
}
input:focus, entry:focus {
  border: 1.5px solid var(--input-focus);
}

badge, .badge {
  background: var(--secondary);
  color: var(--fg);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.badge-primary, badge.primary {
  background: var(--primary);
  color: var(--primary-fg);
}
.badge-success, badge.success {
  background: var(--success);
  color: #ffffff;
}
.badge-warning, badge.warning {
  background: var(--warning);
  color: #ffffff;
}
.badge-danger, .badge-destructive, badge.danger {
  background: var(--destructive);
  color: #ffffff;
}

switch, .switch {
  background: var(--track-bg);
  color: var(--thumb-color);
  border-radius: 12px;
}
switch:checked {
  background: var(--primary);
}

progress, .progress {
  background: var(--track-bg);
  color: var(--primary);
  border-radius: 6px;
}

slider, .slider {
  background: var(--track-bg);
  color: var(--primary);
  border-radius: 4px;
}
)css";

inline const char* DEFAULT_NORD_THEME_CSS = R"css(
:root {
  --bg: #2e3440;
  --fg: #eceff4;
  --text-muted: #d8dee9;
  --fg-subtle: #d8dee9;
  --card-bg: #434c5e;
  --card-border: #4c566a;
  --surface: #3b4252;
  --surface-border: #4c566a;
  --primary: #88c0d0;
  --primary-hover: #8fbcbb;
  --primary-active: #81a1c1;
  --primary-fg: #2e3440;
  --secondary: #4c566a;
  --secondary-hover: #5b677e;
  --secondary-active: #3f4756;
  --secondary-fg: #eceff4;
  --accent: #81a1c1;
  --success: #a3be8c;
  --warning: #ebcb8b;
  --destructive: #bf616a;
  --danger: #bf616a;
  --input-bg: #3b4252;
  --input-border: #4c566a;
  --input-focus: #88c0d0;
  --track-bg: #4c566a;
  --thumb-color: #88c0d0;
  --shadow: rgba(0, 0, 0, 0.35);
  --shadow-color: rgba(0, 0, 0, 0.35);
}
)css";

inline const char* DEFAULT_DRACULA_THEME_CSS = R"css(
:root {
  --bg: #282a36;
  --fg: #f8f8f2;
  --text-muted: #6272a4;
  --fg-subtle: #6272a4;
  --card-bg: #343746;
  --card-border: #44475a;
  --surface: #21222c;
  --surface-border: #44475a;
  --primary: #bd93f9;
  --primary-hover: #caa6fc;
  --primary-active: #a777f5;
  --primary-fg: #282a36;
  --secondary: #6272a4;
  --secondary-hover: #7283b5;
  --secondary-active: #526190;
  --secondary-fg: #f8f8f2;
  --accent: #ff79c6;
  --success: #50fa7b;
  --warning: #ffb86c;
  --destructive: #ff5555;
  --danger: #ff5555;
  --input-bg: #21222c;
  --input-border: #6272a4;
  --input-focus: #bd93f9;
  --track-bg: #44475a;
  --thumb-color: #bd93f9;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_TOKYO_NIGHT_THEME_CSS = R"css(
:root {
  --bg: #1a1b26;
  --fg: #c0caf5;
  --text-muted: #7aa2f7;
  --fg-subtle: #7aa2f7;
  --card-bg: #24283b;
  --card-border: #414868;
  --surface: #16161e;
  --surface-border: #292e42;
  --primary: #7aa2f7;
  --primary-hover: #89b4fa;
  --primary-active: #628be0;
  --primary-fg: #15161e;
  --secondary: #414868;
  --secondary-hover: #565f89;
  --secondary-active: #343b58;
  --secondary-fg: #c0caf5;
  --accent: #bb9af7;
  --success: #9ece6a;
  --warning: #e0af68;
  --destructive: #f7768e;
  --danger: #f7768e;
  --input-bg: #16161e;
  --input-border: #414868;
  --input-focus: #7aa2f7;
  --track-bg: #292e42;
  --thumb-color: #7aa2f7;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_CATPPUCCIN_MOCHA_THEME_CSS = R"css(
:root {
  --bg: #1e1e2e;
  --fg: #cdd6f4;
  --text-muted: #a6adc8;
  --fg-subtle: #a6adc8;
  --card-bg: #313244;
  --card-border: #45475a;
  --surface: #181825;
  --surface-border: #313244;
  --primary: #cba6f7;
  --primary-hover: #d5b4fc;
  --primary-active: #b485ee;
  --primary-fg: #11111b;
  --secondary: #45475a;
  --secondary-hover: #585b70;
  --secondary-active: #313244;
  --secondary-fg: #cdd6f4;
  --accent: #f5c2e7;
  --success: #a6e3a1;
  --warning: #f9e2af;
  --destructive: #f38ba8;
  --danger: #f38ba8;
  --input-bg: #181825;
  --input-border: #45475a;
  --input-focus: #cba6f7;
  --track-bg: #313244;
  --thumb-color: #cba6f7;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_CATPPUCCIN_LATTE_THEME_CSS = R"css(
:root {
  --bg: #eff1f5;
  --fg: #4c4f69;
  --text-muted: #6c6f85;
  --fg-subtle: #6c6f85;
  --card-bg: #ffffff;
  --card-border: #ccd0da;
  --surface: #e6e9ef;
  --surface-border: #ccd0da;
  --primary: #8839ef;
  --primary-hover: #9a52f4;
  --primary-active: #7222df;
  --primary-fg: #ffffff;
  --secondary: #ccd0da;
  --secondary-hover: #bcc0cc;
  --secondary-active: #acb0be;
  --secondary-fg: #4c4f69;
  --accent: #ea76cb;
  --success: #40a02b;
  --warning: #df8e1d;
  --destructive: #d20f39;
  --danger: #d20f39;
  --input-bg: #ffffff;
  --input-border: #bcc0cc;
  --input-focus: #8839ef;
  --track-bg: #dce0e8;
  --thumb-color: #8839ef;
  --shadow: rgba(0, 0, 0, 0.10);
  --shadow-color: rgba(0, 0, 0, 0.10);
}
)css";

inline const char* DEFAULT_EMERALD_THEME_CSS = R"css(
:root {
  --bg: #064e3b;
  --fg: #ecfdf5;
  --text-muted: #a7f3d0;
  --fg-subtle: #a7f3d0;
  --card-bg: #047857;
  --card-border: #10b981;
  --surface: #065f46;
  --surface-border: #10b981;
  --primary: #34d399;
  --primary-hover: #6ee7b7;
  --primary-active: #059669;
  --primary-fg: #064e3b;
  --secondary: #065f46;
  --secondary-hover: #047857;
  --secondary-active: #064e3b;
  --secondary-fg: #ecfdf5;
  --accent: #6ee7b7;
  --success: #34d399;
  --warning: #fbbf24;
  --destructive: #f87171;
  --danger: #f87171;
  --input-bg: #065f46;
  --input-border: #10b981;
  --input-focus: #34d399;
  --track-bg: #065f46;
  --thumb-color: #34d399;
  --shadow: rgba(0, 0, 0, 0.35);
  --shadow-color: rgba(0, 0, 0, 0.35);
}
)css";

inline const char* DEFAULT_OCEAN_THEME_CSS = R"css(
:root {
  --bg: #0b192c;
  --fg: #e0f2fe;
  --text-muted: #7dd3fc;
  --fg-subtle: #7dd3fc;
  --card-bg: #1e3e62;
  --card-border: #00000000;
  --surface: #1e293b;
  --surface-border: #334155;
  --primary: #38bdf8;
  --primary-hover: #7dd3fc;
  --primary-active: #0284c7;
  --primary-fg: #0b192c;
  --secondary: #1e293b;
  --secondary-hover: #334155;
  --secondary-active: #0f172a;
  --secondary-fg: #e0f2fe;
  --accent: #06b6d4;
  --success: #10b981;
  --warning: #f59e0b;
  --destructive: #f43f5e;
  --danger: #f43f5e;
  --input-bg: #1e293b;
  --input-border: #334155;
  --input-focus: #38bdf8;
  --track-bg: #1e293b;
  --thumb-color: #38bdf8;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_SUNSET_THEME_CSS = R"css(
:root {
  --bg: #181124;
  --fg: #fff1f2;
  --text-muted: #fda4af;
  --fg-subtle: #fda4af;
  --card-bg: #35153b;
  --card-border: #501b5a;
  --surface: #241335;
  --surface-border: #3b1b54;
  --primary: #f43f5e;
  --primary-hover: #fb7185;
  --primary-active: #e11d48;
  --primary-fg: #ffffff;
  --secondary: #3b1b54;
  --secondary-hover: #4c226c;
  --secondary-active: #2a113d;
  --secondary-fg: #fff1f2;
  --accent: #fb923c;
  --success: #34d399;
  --warning: #facc15;
  --destructive: #f87171;
  --danger: #f87171;
  --input-bg: #241335;
  --input-border: #3b1b54;
  --input-focus: #f43f5e;
  --track-bg: #3b1b54;
  --thumb-color: #f43f5e;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_MONOKAI_THEME_CSS = R"css(
:root {
  --bg: #272822;
  --fg: #f8f8f2;
  --text-muted: #75715e;
  --fg-subtle: #75715e;
  --card-bg: #3e3d32;
  --card-border: #49483e;
  --surface: #1e1f1c;
  --surface-border: #3e3d32;
  --primary: #a6e22e;
  --primary-hover: #b8ea50;
  --primary-active: #8ac020;
  --primary-fg: #272822;
  --secondary: #49483e;
  --secondary-hover: #5c5b4e;
  --secondary-active: #383730;
  --secondary-fg: #f8f8f2;
  --accent: #f92672;
  --success: #a6e22e;
  --warning: #fd971f;
  --destructive: #f92672;
  --danger: #f92672;
  --input-bg: #1e1f1c;
  --input-border: #49483e;
  --input-focus: #a6e22e;
  --track-bg: #3e3d32;
  --thumb-color: #a6e22e;
  --shadow: rgba(0, 0, 0, 0.40);
  --shadow-color: rgba(0, 0, 0, 0.40);
}
)css";

inline const char* DEFAULT_CYBERPUNK_THEME_CSS = R"css(
:root {
  --bg: #0d0d1a;
  --fg: #00ffcc;
  --text-muted: #ff007f;
  --fg-subtle: #ff007f;
  --card-bg: #1a1a2e;
  --card-border: #ff007f;
  --surface: #16162a;
  --surface-border: #ff007f;
  --primary: #ff007f;
  --primary-hover: #ff3399;
  --primary-active: #cc0066;
  --primary-fg: #ffffff;
  --secondary: #00e5ff;
  --secondary-hover: #33ebff;
  --secondary-active: #00b8cc;
  --secondary-fg: #0d0d1a;
  --accent: #ffe600;
  --success: #00ffcc;
  --warning: #ffe600;
  --destructive: #ff0055;
  --danger: #ff0055;
  --input-bg: #16162a;
  --input-border: #ff007f;
  --input-focus: #00ffcc;
  --track-bg: #1a1a2e;
  --thumb-color: #00ffcc;
  --shadow: rgba(255, 0, 127, 0.35);
  --shadow-color: rgba(255, 0, 127, 0.35);
}
)css";

inline const char* DEFAULT_SOLARIZED_DARK_THEME_CSS = R"css(
:root {
  --bg: #002b36;
  --fg: #839496;
  --text-muted: #586e75;
  --fg-subtle: #586e75;
  --card-bg: #073642;
  --card-border: #586e75;
  --surface: #073642;
  --surface-border: #586e75;
  --primary: #268bd2;
  --primary-hover: #2aa198;
  --primary-active: #1e6ea8;
  --primary-fg: #fdf6e3;
  --secondary: #586e75;
  --secondary-hover: #657b83;
  --secondary-active: #073642;
  --secondary-fg: #fdf6e3;
  --accent: #d33682;
  --success: #859900;
  --warning: #b58900;
  --destructive: #dc322f;
  --danger: #dc322f;
  --input-bg: #073642;
  --input-border: #586e75;
  --input-focus: #268bd2;
  --track-bg: #073642;
  --thumb-color: #268bd2;
  --shadow: rgba(0, 0, 0, 0.35);
  --shadow-color: rgba(0, 0, 0, 0.35);
}
)css";

inline const char* DEFAULT_SOLARIZED_LIGHT_THEME_CSS = R"css(
:root {
  --bg: #fdf6e3;
  --fg: #657b83;
  --text-muted: #93a1a1;
  --fg-subtle: #93a1a1;
  --card-bg: #eee8d5;
  --card-border: #93a1a1;
  --surface: #eee8d5;
  --surface-border: #93a1a1;
  --primary: #268bd2;
  --primary-hover: #2aa198;
  --primary-active: #1e6ea8;
  --primary-fg: #fdf6e3;
  --secondary: #93a1a1;
  --secondary-hover: #839496;
  --secondary-active: #eee8d5;
  --secondary-fg: #073642;
  --accent: #d33682;
  --success: #859900;
  --warning: #b58900;
  --destructive: #dc322f;
  --danger: #dc322f;
  --input-bg: #ffffff;
  --input-border: #93a1a1;
  --input-focus: #268bd2;
  --track-bg: #eee8d5;
  --thumb-color: #268bd2;
  --shadow: rgba(0, 0, 0, 0.12);
  --shadow-color: rgba(0, 0, 0, 0.12);
}
)css";

} // namespace tkblend
