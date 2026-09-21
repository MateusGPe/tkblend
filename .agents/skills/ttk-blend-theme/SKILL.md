---
name: ttk-blend-theme
description: Comprehensive architecture guide and reference patterns for developing native C/C++ TTK theme extensions with Blend2D in tkblend.
---

# TTK Blend2D Native Theme Extension Guide

This skill provides essential guidelines, architecture rules, and reference patterns for developing and debugging native C/C++ TTK theme elements with Blend2D zero-copy rasterization.

## 1. TTK ABI & Element Spec Version Invariant

In Tk 8.5, 8.6, and 9.0 ABI:
- Every `Ttk_ElementSpec` must have its `version` set to `TK_STYLE_VERSION_2` (`2`).
- If `spec->version != TK_STYLE_VERSION_2`, `Ttk_RegisterElement` silently returns failure (`0`), and Tk falls back to default/classic unskinned widgets.

```cpp
#ifndef TK_STYLE_VERSION_2
  enum TTKStyleVersion2 { TK_STYLE_VERSION_2 = 2 };
#endif
#ifndef TTK_LAYOUT_SPEC_VERSION
  #define TTK_LAYOUT_SPEC_VERSION TK_STYLE_VERSION_2
#endif

Ttk_ElementSpec ButtonElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, // MUST be 2 (TK_STYLE_VERSION_2)
    sizeof(ButtonElement),
    ButtonElementOptions,
    ButtonElementGeometry,
    ButtonElementDraw
};
```

## 2. Element Registration Best Practices

1. **Pass `interp` to registration**: Use `Ttk_RegisterElement(interp, theme, name, spec, clientData)` instead of `Ttk_RegisterElementSpec` so registration errors are reported directly to the Tcl interpreter.
2. **Register both unqualified and qualified names**: Register generic names (`button`, `field`, `trough`, `slider`, `thumb`, `pbar`, `bar`, `indicator`) as well as widget-qualified names (`Button.button`, `Entry.field`, `Horizontal.Progressbar.pbar`, `Horizontal.Scale.slider`, etc.) to guarantee matching across layouts.

```cpp
Ttk_RegisterElement(interp, theme, "button", &ButtonElementSpec, nullptr);
Ttk_RegisterElement(interp, theme, "Button.button", &ButtonElementSpec, nullptr);
Ttk_RegisterElement(interp, theme, "trough", &PbarTroughElementSpec, nullptr);
Ttk_RegisterElement(interp, theme, "pbar", &PbarBarElementSpec, nullptr);
Ttk_RegisterElement(interp, theme, "slider", &ScaleSliderElementSpec, nullptr);
Ttk_RegisterElement(interp, theme, "thumb", &ScrollbarThumbElementSpec, nullptr);
```

## 3. Option Specifications & Dynamic Color Parsing

- Use valid `Tk_OptionType` constants (`TK_OPTION_COLOR`, `TK_OPTION_STRING`, `TK_OPTION_RELIEF`, `TK_OPTION_PIXELS`).
- Always implement hex color parsing (`parse_hex_color`) in draw procedures to support dynamic user-defined colors in addition to named variants (`Primary`, `Secondary`, `Destructive`, `Ghost`).

```cpp
static bool parse_hex_color(const std::string& str, uint32_t& out_argb) {
    if (str.empty()) return false;
    std::string s = str;
    if (s[0] == '#') s = s.substr(1);
    if (s.length() != 6 && s.length() != 8 && s.length() != 3) return false;
    if (s.length() == 3) {
        std::string exp;
        for (char c : s) { exp += c; exp += c; }
        s = exp;
    }
    try {
        unsigned long val = std::stoul(s, nullptr, 16);
        if (s.length() == 6) {
            out_argb = 0xFF000000u | static_cast<uint32_t>(val);
        } else {
            out_argb = static_cast<uint32_t>(val);
        }
        return true;
    } catch (...) {
        return false;
    }
}
```

## 4. Tcl Style Script Color Invariants

Tk's sub-elements (like `Button.label`, `Checkbutton.label`) invoke `Tk_GetColor` to render foreground and background.
- **Never** configure styles with abstract tokens (e.g. `ttk::style configure Accent.TButton -background "primary"`). Tk will fail to resolve `"primary"` as an X11 color name, resulting in solid black text or styling errors.
- **Always** format and pass valid hex color strings (e.g. `-background "#6366f1" -foreground "#ffffff"`).

## 5. Container & Ancestor Background Resolution

On platforms where X11/GDI blits lack destination alpha compositing (opaque `XPutImage`):
- `Tk_GetOption(tkwin, "background", ...)` only queries the Xrm option database and returns `NULL` for TTK widgets.
- Use `Tk_Class(curr)` to inspect the widget hierarchy for container classes:
  - `"TLabelframe"`, `"Card"`, `"Notebook"` -> pre-fill background with `card_bg`.
  - Fallback -> `bg_color`.

## 6. Official Tk Reference Tree

The repository contains the complete official Tk 8.6/9 source tree under `REFERENCE ONLY/` for inspecting built-in themes (`ttkClamTheme.c`, `ttkElements.c`, `ttkTheme.c`).
