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

} // namespace tkblend

