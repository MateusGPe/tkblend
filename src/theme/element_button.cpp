#include "element_common.h"
#include <sstream>
#include <iomanip>

namespace tkblend {

struct ButtonElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* reliefObj;
    Tcl_Obj* borderWidthObj;
    Tcl_Obj* variantObj;
};

static Ttk_ElementOptionSpec ButtonElementOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ButtonElement, backgroundObj), "" },
    { "-relief", TK_OPTION_STRING, offsetof(ButtonElement, reliefObj), "flat" },
    { "-borderwidth", TK_OPTION_STRING, offsetof(ButtonElement, borderWidthObj), "1" },
    { "-variant", TK_OPTION_STRING, offsetof(ButtonElement, variantObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

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
    } catch (const std::invalid_argument&) {
        return false;
    } catch (const std::out_of_range&) {
        return false;
    }
}

static void ButtonElementGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 40;
    if (heightPtr) *heightPtr = 28;
    if (paddingPtr) {
        paddingPtr->left   = 16;
        paddingPtr->top    = 7;
        paddingPtr->right  = 16;
        paddingPtr->bottom = 7;
    }
}

static void ButtonElementDraw(
    void* /*clientData*/, void* elementRecord,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();
    auto* elem = static_cast<ButtonElement*>(elementRecord);

    enum class ButtonVariant { Standard, Primary, Destructive, Secondary, Ghost, Outline, Custom };
    ButtonVariant variant = ButtonVariant::Standard;
    uint32_t custom_col = 0;

    if (elem && elem->variantObj) {
        const char* var_str = Tcl_GetString(elem->variantObj);
        if (var_str && var_str[0] != '\0') {
            std::string v(var_str);
            std::transform(v.begin(), v.end(), v.begin(), ::tolower);
            if (v.find("ghost") != std::string::npos) {
                variant = ButtonVariant::Ghost;
            } else if (v.find("outline") != std::string::npos) {
                variant = ButtonVariant::Outline;
            } else if (v.find("accent") != std::string::npos || v.find("primary") != std::string::npos || v.find("indigo") != std::string::npos) {
                variant = ButtonVariant::Primary;
            } else if (v.find("destruct") != std::string::npos || v.find("danger") != std::string::npos || v.find("red") != std::string::npos || v.find("rose") != std::string::npos) {
                variant = ButtonVariant::Destructive;
            } else if (v.find("secondary") != std::string::npos) {
                variant = ButtonVariant::Secondary;
            }
        }
    }

    if (variant == ButtonVariant::Standard && elem && elem->backgroundObj) {
        const char* bg_str = Tcl_GetString(elem->backgroundObj);
        if (bg_str && bg_str[0] != '\0') {
            std::string s(bg_str);
            std::transform(s.begin(), s.end(), s.begin(), ::tolower);
            if (s.find("accent") != std::string::npos || s.find("primary") != std::string::npos || s.find("indigo") != std::string::npos) {
                variant = ButtonVariant::Primary;
            } else if (s.find("destruct") != std::string::npos || s.find("danger") != std::string::npos || s.find("red") != std::string::npos || s.find("rose") != std::string::npos) {
                variant = ButtonVariant::Destructive;
            } else if (s.find("ghost") != std::string::npos) {
                variant = ButtonVariant::Ghost;
            } else if (s.find("outline") != std::string::npos) {
                variant = ButtonVariant::Outline;
            } else if (s.find("secondary") != std::string::npos) {
                variant = ButtonVariant::Secondary;
            } else if (s[0] == '#') {
                uint32_t parsed = 0;
                if (parse_hex_color(s, parsed)) {
                    if ((parsed & 0x00FFFFFF) == (cfg.primary_color & 0x00FFFFFF)) {
                        variant = ButtonVariant::Primary;
                    } else if ((parsed & 0x00FFFFFF) == (cfg.destructive_color & 0x00FFFFFF)) {
                        variant = ButtonVariant::Destructive;
                    } else if ((parsed & 0x00FFFFFF) == (cfg.secondary_color & 0x00FFFFFF)) {
                        variant = ButtonVariant::Secondary;
                    } else {
                        variant = ButtonVariant::Custom;
                        custom_col = parsed;
                    }
                }
            }
        }
    }

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        double r = cfg.button_radius;
        if (r * 2.0 > w) r = w / 2.0;
        if (r * 2.0 > h) r = h / 2.0;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);
        bool focus    = is_focus(state);

        uint32_t fill_top, fill_bot, border_color;
        bool has_fill = true;
        bool has_border = true;

        switch (variant) {
        case ButtonVariant::Primary:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = cfg.primary_active;
                fill_bot = blend_colors(cfg.primary_active, 0xFF000000, 0.2f);
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = blend_colors(cfg.primary_hover, 0xFFFFFFFF, 0.1f);
                fill_bot = cfg.primary_color;
                border_color = cfg.primary_hover;
            } else {
                fill_top = cfg.primary_color;
                fill_bot = cfg.primary_active;
                border_color = blend_colors(cfg.primary_color, 0xFFFFFFFF, 0.15f);
            }
            break;

        case ButtonVariant::Destructive:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = cfg.destructive_active;
                fill_bot = blend_colors(cfg.destructive_active, 0xFF000000, 0.2f);
                border_color = cfg.destructive_active;
            } else if (hover) {
                fill_top = cfg.destructive_hover;
                fill_bot = cfg.destructive_color;
                border_color = cfg.destructive_hover;
            } else {
                fill_top = cfg.destructive_color;
                fill_bot = cfg.destructive_active;
                border_color = blend_colors(cfg.destructive_color, 0xFFFFFFFF, 0.15f);
            }
            break;

        case ButtonVariant::Secondary:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = fill_bot = blend_colors(cfg.secondary_color, 0xFF000000, 0.2f);
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = blend_colors(cfg.secondary_hover, 0xFFFFFFFF, 0.05f);
                fill_bot = cfg.secondary_hover;
                border_color = cfg.primary_hover;
            } else {
                fill_top = blend_colors(cfg.secondary_color, 0xFFFFFFFF, 0.03f);
                fill_bot = cfg.secondary_color;
                border_color = cfg.card_border;
            }
            break;

        case ButtonVariant::Ghost:
            if (disabled) {
                has_fill = false;
                has_border = false;
                fill_top = fill_bot = 0;
                border_color = 0;
            } else if (pressed) {
                fill_top = fill_bot = cfg.secondary_hover;
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = fill_bot = blend_colors(cfg.bg_color, cfg.secondary_hover, 0.8f);
                border_color = cfg.card_border;
            } else {
                has_fill = false;
                has_border = false;
                fill_top = fill_bot = 0;
                border_color = 0;
            }
            break;

        case ButtonVariant::Outline:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = fill_bot = cfg.secondary_hover;
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = fill_bot = blend_colors(cfg.bg_color, cfg.secondary_hover, 0.5f);
                border_color = cfg.primary_hover;
            } else {
                fill_top = fill_bot = cfg.card_bg;
                border_color = cfg.input_border;
            }
            break;

        case ButtonVariant::Custom:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = blend_colors(custom_col, 0xFF000000, 0.25f);
                fill_bot = blend_colors(custom_col, 0xFF000000, 0.35f);
                border_color = fill_top;
            } else if (hover) {
                fill_top = blend_colors(custom_col, 0xFFFFFFFF, 0.12f);
                fill_bot = custom_col;
                border_color = blend_colors(custom_col, 0xFFFFFFFF, 0.2f);
            } else {
                fill_top = custom_col;
                fill_bot = blend_colors(custom_col, 0xFF000000, 0.12f);
                border_color = blend_colors(custom_col, 0xFFFFFFFF, 0.15f);
            }
            break;

        case ButtonVariant::Standard:
        default:
            if (disabled) {
                fill_top = fill_bot = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_top = fill_bot = blend_colors(cfg.secondary_color, 0xFF000000, 0.15f);
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = blend_colors(cfg.secondary_hover, 0xFFFFFFFF, 0.08f);
                fill_bot = cfg.secondary_hover;
                border_color = cfg.primary_hover;
            } else {
                fill_top = blend_colors(cfg.secondary_color, 0xFFFFFFFF, 0.04f);
                fill_bot = cfg.secondary_color;
                border_color = cfg.card_border;
            }
            break;
        }

        // Draw modern soft drop shadow
        if (cfg.enable_shadows && !pressed && !disabled && variant != ButtonVariant::Ghost) {
            ctx.save();
            BLPath shadowPath;
            double s_offset = (variant == ButtonVariant::Primary) ? 2.5 : 2.0;
            shadowPath.add_round_rect(BLRoundRect(1.0, s_offset, w - 2.0, h - 2.0, r, r));
            uint32_t s_col = (variant == ButtonVariant::Primary) ? 0x406366F1 : cfg.shadow_color;
            ctx.set_fill_style(to_bl_rgba(s_col));
            ctx.fill_path(shadowPath);
            ctx.restore();
        }

        // Main button body
        BLPath bodyPath;
        double pad = 1.0;
        double by = pressed ? (pad + 1.0) : pad;
        bodyPath.add_round_rect(BLRoundRect(pad, by, w - (pad * 2.0), h - (pad * 2.0) - (pressed ? 1.0 : 0.0), r, r));

        if (has_fill) {
            // Rich linear lighting gradient
            BLGradient grad(BLLinearGradientValues(0, by, 0, by + h));
            grad.add_stop(0.0, to_bl_rgba(fill_top));
            grad.add_stop(1.0, to_bl_rgba(fill_bot));

            ctx.set_fill_style(grad);
            ctx.fill_path(bodyPath);
        }

        if (has_border) {
            // Crisp 1px border stroke
            ctx.set_stroke_width(1.0);
            ctx.set_stroke_style(to_bl_rgba(border_color));
            ctx.stroke_path(bodyPath);
        }

        // Top specular edge highlight (1px inset)
        if (has_fill && !pressed && !disabled && h > 16 && variant != ButtonVariant::Ghost) {
            BLPath highlightPath;
            highlightPath.move_to(pad + r * 0.6, by + 1.0);
            highlightPath.line_to(w - pad - r * 0.6, by + 1.0);
            ctx.set_stroke_width(1.0);
            uint32_t hi_col = (variant == ButtonVariant::Primary) ? 0x40FFFFFF : 0x1AFFFFFF;
            ctx.set_stroke_style(to_bl_rgba(hi_col));
            ctx.stroke_path(highlightPath);
        }

        // Radiant focus ring
        if (focus && !disabled) {
            BLPath focusPath;
            focusPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r + 0.5, r + 0.5));
            ctx.set_stroke_width(cfg.focus_ring_width);
            ctx.set_stroke_style(to_bl_rgba(cfg.focus_ring_color));
            ctx.stroke_path(focusPath);
        }
    });
}

Ttk_ElementSpec ButtonElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ButtonElement),
    ButtonElementOptions,
    ButtonElementGeometry,
    ButtonElementDraw
};

} // namespace tkblend
