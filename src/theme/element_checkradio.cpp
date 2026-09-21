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
        bool disabled = is_disabled(state);
        bool selected = is_selected(state);
        bool hover    = is_active(state);
        bool pressed  = is_pressed(state);
        bool focus    = is_focus(state);

        double size = 18.0;
        if (size > w) size = w;
        if (size > h) size = h;
        double x = (w - size) / 2.0;
        double y = (h - size) / 2.0;
        double r = cfg.check_radius;

        BLPath boxPath;
        boxPath.add_round_rect(BLRoundRect(x + 0.5, y + 0.5, size - 1.0, size - 1.0, r, r));

        uint32_t fill_color;
        uint32_t border_color;

        if (disabled) {
            fill_color   = cfg.disabled_bg;
            border_color = cfg.card_border;
        } else if (selected) {
            fill_color   = pressed ? cfg.primary_active : (hover ? cfg.primary_hover : cfg.primary_color);
            border_color = pressed ? cfg.primary_color : cfg.primary_hover;
        } else {
            fill_color   = pressed ? cfg.secondary_hover : cfg.input_bg;
            border_color = hover ? cfg.primary_hover : cfg.input_border;
        }

        ctx.set_fill_style(to_bl_rgba(fill_color));
        ctx.fill_path(boxPath);
        ctx.set_stroke_width(1.2);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_path(boxPath);

        // Draw antialiased Vector Checkmark when selected
        if (selected) {
            uint32_t check_col = disabled ? cfg.disabled_fg : cfg.primary_fg;
            BLPath checkPath;
            double cx = x + 0.5;
            double cy = y + 0.5;
            double bw = size - 1.0;
            double bh = size - 1.0;

            checkPath.move_to(cx + bw * 0.24, cy + bh * 0.52);
            checkPath.line_to(cx + bw * 0.44, cy + bh * 0.74);
            checkPath.line_to(cx + bw * 0.78, cy + bh * 0.28);

            ctx.set_stroke_width(2.2);
            ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
            ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
            ctx.set_stroke_style(to_bl_rgba(check_col));
            ctx.stroke_path(checkPath);
        }

        // Focus ring
        if (focus && !disabled) {
            BLPath focusPath;
            focusPath.add_round_rect(BLRoundRect(x - 0.5, y - 0.5, size + 1.0, size + 1.0, r + 1.0, r + 1.0));
            ctx.set_stroke_width(1.5);
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

        uint32_t fill_color;
        uint32_t border_color;

        if (disabled) {
            fill_color   = cfg.disabled_bg;
            border_color = cfg.card_border;
        } else if (selected) {
            fill_color   = pressed ? cfg.primary_active : (hover ? cfg.primary_hover : cfg.primary_color);
            border_color = pressed ? cfg.primary_color : cfg.primary_hover;
        } else {
            fill_color   = pressed ? cfg.secondary_hover : cfg.input_bg;
            border_color = hover ? cfg.primary_hover : cfg.input_border;
        }

        BLCircle outerCircle(cx, cy, outer_radius);
        ctx.set_fill_style(to_bl_rgba(fill_color));
        ctx.fill_circle(outerCircle);
        ctx.set_stroke_width(1.2);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_circle(outerCircle);

        // Draw inner dot when selected
        if (selected) {
            uint32_t dot_col = disabled ? cfg.disabled_fg : cfg.primary_fg;
            double inner_radius = outer_radius * 0.45;
            BLCircle innerCircle(cx, cy, inner_radius);
            ctx.set_fill_style(to_bl_rgba(dot_col));
            ctx.fill_circle(innerCircle);
        }

        // Focus ring
        if (focus && !disabled) {
            BLCircle focusCircle(cx, cy, outer_radius + 1.2);
            ctx.set_stroke_width(1.5);
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

} // namespace tkblend
