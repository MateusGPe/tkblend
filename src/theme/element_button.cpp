#include "element_common.h"
#include <sstream>
#include <iomanip>

namespace tkblend {

struct ButtonElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* reliefObj;
    Tcl_Obj* borderWidthObj;
};

static Ttk_ElementOptionSpec ButtonElementOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ButtonElement, backgroundObj), "" },
    { "-relief", TK_OPTION_STRING, offsetof(ButtonElement, reliefObj), "flat" },
    { "-borderwidth", TK_OPTION_STRING, offsetof(ButtonElement, borderWidthObj), "1" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

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

    bool is_primary = false;
    if (elem && elem->backgroundObj) {
        const char* bg_str = Tcl_GetString(elem->backgroundObj);
        if (bg_str && bg_str[0] != '\0') {
            std::string s(bg_str);
            if (s == "primary" || s == "accent" || s.find("blue") != std::string::npos) {
                is_primary = true;
            } else if (s[0] == '#') {
                // Check if background hex matches primary
                std::ostringstream ss;
                ss << "#" << std::hex << std::setfill('0') << std::setw(6) << (cfg.primary_color & 0x00FFFFFF);
                if (s == ss.str()) {
                    is_primary = true;
                }
            }
        }
    }

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        double r = cfg.button_radius;
        if (r * 2.0 > w) r = w / 2.0;
        if (r * 2.0 > h) r = h / 2.0;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);
        bool focus    = is_focus(state);

        uint32_t fill_color;
        uint32_t border_color;

        if (is_primary) {
            if (disabled) {
                fill_color   = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_color   = cfg.primary_active;
                border_color = cfg.primary_color;
            } else if (hover) {
                fill_color   = cfg.primary_hover;
                border_color = cfg.primary_active;
            } else {
                fill_color   = cfg.primary_color;
                border_color = cfg.primary_hover;
            }
        } else {
            if (disabled) {
                fill_color   = cfg.disabled_bg;
                border_color = cfg.card_border;
            } else if (pressed) {
                fill_color   = blend_colors(cfg.secondary_color, 0xFF000000, 0.15f);
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_color   = cfg.secondary_hover;
                border_color = cfg.primary_color;
            } else {
                fill_color   = cfg.secondary_color;
                border_color = cfg.card_border;
            }
        }

        // Draw soft drop shadow
        if (cfg.enable_shadows && !pressed && !disabled) {
            ctx.save();
            BLPath shadowPath;
            shadowPath.add_round_rect(BLRoundRect(1.0, 2.0, w - 2.0, h - 2.5, r, r));
            ctx.set_fill_style(to_bl_rgba(cfg.shadow_color));
            ctx.fill_path(shadowPath);
            ctx.restore();
        }

        // Main button body
        BLPath bodyPath;
        double pad = 1.0;
        bodyPath.add_round_rect(BLRoundRect(pad, pad, w - (pad * 2.0), h - (pad * 2.0), r, r));

        // Subtle vertical lighting gradient
        BLGradient grad(BLLinearGradientValues(0, 0, 0, h));
        uint32_t top_col = pressed ? fill_color : blend_colors(fill_color, 0xFFFFFFFF, 0.05f);
        uint32_t bot_col = pressed ? blend_colors(fill_color, 0xFF000000, 0.08f) : fill_color;
        grad.add_stop(0.0, to_bl_rgba(top_col));
        grad.add_stop(1.0, to_bl_rgba(bot_col));

        ctx.set_fill_style(grad);
        ctx.fill_path(bodyPath);

        // Crisp 1px inner/outer border
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_path(bodyPath);

        // Focus ring illumination
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
