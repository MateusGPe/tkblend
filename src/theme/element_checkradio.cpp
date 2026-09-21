#include "element_common.h"

namespace tkblend {

struct IndicatorElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* colorObj;
};

static Ttk_ElementOptionSpec IndicatorOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(IndicatorElement, backgroundObj), "" },
    { "-indicatorcolor", TK_OPTION_STRING, offsetof(IndicatorElement, colorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void CheckIndicatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 20;
    if (heightPtr) *heightPtr = 20;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 8;
        paddingPtr->bottom = 2;
    }
}

static void CheckIndicatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled  = is_disabled(state);
        bool selected  = is_selected(state);
        bool alternate = is_alternate(state);
        bool hover     = is_active(state);
        bool pressed   = is_pressed(state);
        bool focus     = is_focus(state);
        bool checked_or_alt = selected || alternate;

        double size = 18.0;
        if (size > w) size = w;
        if (size > h) size = h;
        double x = std::floor((w - size) / 2.0);
        double y = std::floor((h - size) / 2.0);
        double r = cfg.check_radius;

        BLPath boxPath;
        boxPath.add_round_rect(BLRoundRect(x + 0.5, y + 0.5, size - 1.0, size - 1.0, r, r));

        uint32_t fill_top, fill_bot, border_color;

        if (disabled) {
            fill_top = fill_bot = cfg.disabled_bg;
            border_color = cfg.card_border;
        } else if (checked_or_alt) {
            if (pressed) {
                fill_top = fill_bot = cfg.primary_active;
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = cfg.primary_hover;
                fill_bot = cfg.primary_color;
                border_color = cfg.primary_hover;
            } else {
                fill_top = cfg.primary_color;
                fill_bot = cfg.primary_active;
                border_color = cfg.primary_color;
            }
        } else {
            fill_top = fill_bot = pressed ? cfg.secondary_hover : cfg.input_bg;
            border_color = hover ? cfg.primary_hover : cfg.input_border;
        }

        BLGradient grad(BLLinearGradientValues(x, y, x, y + size));
        grad.add_stop(0.0, to_bl_rgba(fill_top));
        grad.add_stop(1.0, to_bl_rgba(fill_bot));

        ctx.set_fill_style(grad);
        ctx.fill_path(boxPath);
        ctx.set_stroke_width(1.2);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_path(boxPath);

        // Draw crisp antialiased Vector Checkmark when selected or Dash when alternate
        if (selected) {
            uint32_t check_col = disabled ? cfg.disabled_fg : cfg.primary_fg;
            BLPath checkPath;
            double cx = x + 0.5;
            double cy = y + 0.5;
            double bw = size - 1.0;
            double bh = size - 1.0;

            checkPath.move_to(cx + bw * 0.22, cy + bh * 0.50);
            checkPath.line_to(cx + bw * 0.42, cy + bh * 0.72);
            checkPath.line_to(cx + bw * 0.78, cy + bh * 0.26);

            ctx.set_stroke_width(2.2);
            ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
            ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
            ctx.set_stroke_style(to_bl_rgba(check_col));
            ctx.stroke_path(checkPath);
        } else if (alternate) {
            uint32_t dash_col = disabled ? cfg.disabled_fg : cfg.primary_fg;
            BLPath dashPath;
            double cx = x + 0.5;
            double cy = y + 0.5;
            double bw = size - 1.0;
            double bh = size - 1.0;

            dashPath.move_to(cx + bw * 0.24, cy + bh * 0.50);
            dashPath.line_to(cx + bw * 0.76, cy + bh * 0.50);

            ctx.set_stroke_width(2.2);
            ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
            ctx.set_stroke_style(to_bl_rgba(dash_col));
            ctx.stroke_path(dashPath);
        }

        // Radiant focus ring
        if (focus && !disabled) {
            BLPath focusPath;
            focusPath.add_round_rect(BLRoundRect(x - 0.5, y - 0.5, size + 1.0, size + 1.0, r + 1.0, r + 1.0));
            ctx.set_stroke_width(cfg.focus_ring_width);
            ctx.set_stroke_style(to_bl_rgba(cfg.focus_ring_color));
            ctx.stroke_path(focusPath);
        }
    });
}

Ttk_ElementSpec CheckIndicatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(IndicatorElement),
    IndicatorOptions,
    CheckIndicatorGeometry,
    CheckIndicatorDraw
};

static void RadioIndicatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 20;
    if (heightPtr) *heightPtr = 20;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 8;
        paddingPtr->bottom = 2;
    }
}

static void RadioIndicatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool selected = is_selected(state);
        bool hover    = is_active(state);
        bool pressed  = is_pressed(state);
        bool focus    = is_focus(state);

        double size = 18.0;
        if (size > w) size = w;
        if (size > h) size = h;
        double cx = w / 2.0;
        double cy = h / 2.0;
        double outer_radius = (size - 2.0) / 2.0;

        uint32_t fill_top, fill_bot, border_color;

        if (disabled) {
            fill_top = fill_bot = cfg.disabled_bg;
            border_color = cfg.card_border;
        } else if (selected) {
            if (pressed) {
                fill_top = fill_bot = cfg.primary_active;
                border_color = cfg.primary_active;
            } else if (hover) {
                fill_top = cfg.primary_hover;
                fill_bot = cfg.primary_color;
                border_color = cfg.primary_hover;
            } else {
                fill_top = cfg.primary_color;
                fill_bot = cfg.primary_active;
                border_color = cfg.primary_color;
            }
        } else {
            fill_top = fill_bot = pressed ? cfg.secondary_hover : cfg.input_bg;
            border_color = hover ? cfg.primary_hover : cfg.input_border;
        }

        BLCircle outerCircle(cx, cy, outer_radius);
        BLGradient grad(BLLinearGradientValues(cx, cy - outer_radius, cx, cy + outer_radius));
        grad.add_stop(0.0, to_bl_rgba(fill_top));
        grad.add_stop(1.0, to_bl_rgba(fill_bot));

        ctx.set_fill_style(grad);
        ctx.fill_circle(outerCircle);
        ctx.set_stroke_width(1.2);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_circle(outerCircle);

        // Draw inner dot when selected
        if (selected) {
            uint32_t dot_col = disabled ? cfg.disabled_fg : cfg.primary_fg;
            double inner_radius = outer_radius * 0.44;
            BLCircle innerCircle(cx, cy, inner_radius);
            ctx.set_fill_style(to_bl_rgba(dot_col));
            ctx.fill_circle(innerCircle);
        }

        // Radiant focus ring
        if (focus && !disabled) {
            BLCircle focusCircle(cx, cy, outer_radius + 1.2);
            ctx.set_stroke_width(cfg.focus_ring_width);
            ctx.set_stroke_style(to_bl_rgba(cfg.focus_ring_color));
            ctx.stroke_circle(focusCircle);
        }
    });
}

Ttk_ElementSpec RadioIndicatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(IndicatorElement),
    IndicatorOptions,
    RadioIndicatorGeometry,
    RadioIndicatorDraw
};

// ============================================================================
// Switch Indicator Element (Modern Pill Toggle)
// ============================================================================
static void SwitchIndicatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 40;
    if (heightPtr) *heightPtr = 24;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 8;
        paddingPtr->bottom = 2;
    }
}

static void SwitchIndicatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool selected = is_selected(state);
        bool hover    = is_active(state);
        bool pressed  = is_pressed(state);
        bool focus    = is_focus(state);

        double track_w = 38.0;
        double track_h = 22.0;
        if (track_w > w) track_w = w;
        if (track_h > h) track_h = h;

        double x = std::floor((w - track_w) / 2.0);
        double y = std::floor((h - track_h) / 2.0);
        double r = track_h / 2.0;

        BLPath trackPath;
        trackPath.add_round_rect(BLRoundRect(x + 0.5, y + 0.5, track_w - 1.0, track_h - 1.0, r, r));

        uint32_t fill_color, border_color;
        if (disabled) {
            fill_color   = cfg.disabled_bg;
            border_color = cfg.card_border;
        } else if (selected) {
            if (pressed) {
                fill_color = border_color = cfg.primary_active;
            } else if (hover) {
                fill_color = border_color = cfg.primary_hover;
            } else {
                fill_color = border_color = cfg.primary_color;
            }
        } else {
            fill_color   = pressed ? cfg.secondary_hover : cfg.input_bg;
            border_color = hover ? cfg.primary_hover : cfg.input_border;
        }

        ctx.set_fill_style(to_bl_rgba(fill_color));
        ctx.fill_path(trackPath);
        ctx.set_stroke_width(1.2);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_path(trackPath);

        // Circular Thumb
        double thumb_radius = (track_h - 6.0) / 2.0;
        double thumb_cx = selected
            ? (x + track_w - 3.0 - thumb_radius)
            : (x + 3.0 + thumb_radius);
        double thumb_cy = y + track_h / 2.0;

        uint32_t thumb_color;
        if (disabled) {
            thumb_color = cfg.disabled_fg;
        } else if (selected) {
            thumb_color = cfg.primary_fg;
        } else {
            thumb_color = hover ? cfg.fg_color : cfg.thumb_color;
        }

        // Thumb soft shadow
        if (cfg.enable_shadows && !disabled) {
            BLCircle shadowCircle(thumb_cx, thumb_cy + 1.0, thumb_radius);
            ctx.set_fill_style(to_bl_rgba(0x2A000000));
            ctx.fill_circle(shadowCircle);
        }

        BLCircle thumbCircle(thumb_cx, thumb_cy, thumb_radius);
        ctx.set_fill_style(to_bl_rgba(thumb_color));
        ctx.fill_circle(thumbCircle);

        // Focus Halo Ring
        if (focus && !disabled) {
            BLPath focusPath;
            focusPath.add_round_rect(BLRoundRect(x - 1.0, y - 1.0, track_w + 2.0, track_h + 2.0, r + 1.5, r + 1.5));
            ctx.set_stroke_width(cfg.focus_ring_width);
            ctx.set_stroke_style(to_bl_rgba(cfg.focus_ring_color));
            ctx.stroke_path(focusPath);
        }
    });
}

Ttk_ElementSpec SwitchIndicatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(IndicatorElement),
    IndicatorOptions,
    SwitchIndicatorGeometry,
    SwitchIndicatorDraw
};

} // namespace tkblend
