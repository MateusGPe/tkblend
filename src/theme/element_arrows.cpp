#include "element_common.h"

namespace tkblend {

struct ArrowElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* arrowColorObj;
};

static Ttk_ElementOptionSpec ArrowElementOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ArrowElement, backgroundObj), "" },
    { "-arrowcolor", TK_OPTION_STRING, offsetof(ArrowElement, arrowColorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

// ============================================================================
// Combobox Down Arrow Element
// ============================================================================
static void ComboboxDownArrowGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 22;
    if (heightPtr) *heightPtr = 24;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 4;
        paddingPtr->bottom = 2;
    }
}

static void ComboboxDownArrowDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);

        // Hover/pressed subtle action pill behind arrow
        if (!disabled && (hover || pressed)) {
            BLPath hoverPill;
            double pad = 2.0;
            hoverPill.add_round_rect(BLRoundRect(pad, pad, w - pad * 2.0, h - pad * 2.0, 4.0, 4.0));
            uint32_t bg_tint = pressed ? blend_colors(cfg.primary_active, 0x33000000, 0.5f)
                                       : blend_colors(cfg.secondary_hover, cfg.primary_color, 0.2f);
            ctx.set_fill_style(to_bl_rgba(bg_tint));
            ctx.fill_path(hoverPill);
        }

        // Draw antialiased vector chevron
        double cx = w / 2.0;
        double cy = h / 2.0;
        double sz = 3.5;

        BLPath arrowPath;
        arrowPath.move_to(cx - sz, cy - sz * 0.5);
        arrowPath.line_to(cx, cy + sz * 0.5);
        arrowPath.line_to(cx + sz, cy - sz * 0.5);

        uint32_t arrow_col = disabled ? cfg.disabled_fg
                                      : (pressed ? cfg.primary_fg
                                                 : (hover ? cfg.primary_hover : cfg.fg_color));

        ctx.set_stroke_width(1.75);
        ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
        ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
        ctx.set_stroke_style(to_bl_rgba(arrow_col));
        ctx.stroke_path(arrowPath);
    });
}

Ttk_ElementSpec ComboboxDownArrowElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ArrowElement),
    ArrowElementOptions,
    ComboboxDownArrowGeometry,
    ComboboxDownArrowDraw
};

// ============================================================================
// Spinbox Up & Down Arrow Elements
// ============================================================================
static void SpinboxArrowGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 18;
    if (heightPtr) *heightPtr = 11;
    if (paddingPtr) {
        paddingPtr->left   = 1;
        paddingPtr->top    = 1;
        paddingPtr->right  = 2;
        paddingPtr->bottom = 1;
    }
}

static void SpinboxUpArrowDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);

        if (!disabled && (hover || pressed)) {
            BLPath hoverPill;
            hoverPill.add_round_rect(BLRoundRect(1.0, 1.0, w - 2.0, h - 2.0, 3.0, 3.0));
            uint32_t bg_tint = pressed ? blend_colors(cfg.primary_active, 0x33000000, 0.5f)
                                       : blend_colors(cfg.secondary_hover, cfg.primary_color, 0.2f);
            ctx.set_fill_style(to_bl_rgba(bg_tint));
            ctx.fill_path(hoverPill);
        }

        double cx = w / 2.0;
        double cy = h / 2.0 + 0.5;
        double sz = 2.8;

        BLPath arrowPath;
        arrowPath.move_to(cx - sz, cy + sz * 0.5);
        arrowPath.line_to(cx, cy - sz * 0.5);
        arrowPath.line_to(cx + sz, cy + sz * 0.5);

        uint32_t arrow_col = disabled ? cfg.disabled_fg
                                      : (pressed ? cfg.primary_fg
                                                 : (hover ? cfg.primary_hover : cfg.fg_color));

        ctx.set_stroke_width(1.5);
        ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
        ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
        ctx.set_stroke_style(to_bl_rgba(arrow_col));
        ctx.stroke_path(arrowPath);
    });
}

static void SpinboxDownArrowDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);

        if (!disabled && (hover || pressed)) {
            BLPath hoverPill;
            hoverPill.add_round_rect(BLRoundRect(1.0, 1.0, w - 2.0, h - 2.0, 3.0, 3.0));
            uint32_t bg_tint = pressed ? blend_colors(cfg.primary_active, 0x33000000, 0.5f)
                                       : blend_colors(cfg.secondary_hover, cfg.primary_color, 0.2f);
            ctx.set_fill_style(to_bl_rgba(bg_tint));
            ctx.fill_path(hoverPill);
        }

        double cx = w / 2.0;
        double cy = h / 2.0 - 0.5;
        double sz = 2.8;

        BLPath arrowPath;
        arrowPath.move_to(cx - sz, cy - sz * 0.5);
        arrowPath.line_to(cx, cy + sz * 0.5);
        arrowPath.line_to(cx + sz, cy - sz * 0.5);

        uint32_t arrow_col = disabled ? cfg.disabled_fg
                                      : (pressed ? cfg.primary_fg
                                                 : (hover ? cfg.primary_hover : cfg.fg_color));

        ctx.set_stroke_width(1.5);
        ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
        ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
        ctx.set_stroke_style(to_bl_rgba(arrow_col));
        ctx.stroke_path(arrowPath);
    });
}

Ttk_ElementSpec SpinboxUpArrowElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ArrowElement),
    ArrowElementOptions,
    SpinboxArrowGeometry,
    SpinboxUpArrowDraw
};

Ttk_ElementSpec SpinboxDownArrowElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ArrowElement),
    ArrowElementOptions,
    SpinboxArrowGeometry,
    SpinboxDownArrowDraw
};

// ============================================================================
// Spinbox Buttons Container Element
// ============================================================================
static void SpinboxButtonsGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 20;
    if (heightPtr) *heightPtr = 24;
    if (paddingPtr) {
        paddingPtr->left   = 1;
        paddingPtr->top    = 1;
        paddingPtr->right  = 1;
        paddingPtr->bottom = 1;
    }
}

static void SpinboxButtonsDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        // Subtle left divider line
        BLPath divPath;
        divPath.move_to(0.5, 3.0);
        divPath.line_to(0.5, h - 3.0);
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.input_border));
        ctx.stroke_path(divPath);
    });
}

Ttk_ElementSpec SpinboxButtonsElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ArrowElement),
    ArrowElementOptions,
    SpinboxButtonsGeometry,
    SpinboxButtonsDraw
};

// ============================================================================
// Menubutton Indicator Element (Dropdown Chevron)
// ============================================================================
static void MenubuttonIndicatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 16;
    if (heightPtr) *heightPtr = 20;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 6;
        paddingPtr->bottom = 2;
    }
}

static void MenubuttonIndicatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);

        double cx = w / 2.0;
        double cy = h / 2.0;
        double sz = 3.2;

        BLPath arrowPath;
        arrowPath.move_to(cx - sz, cy - sz * 0.4);
        arrowPath.line_to(cx, cy + sz * 0.5);
        arrowPath.line_to(cx + sz, cy - sz * 0.4);

        uint32_t arrow_col = disabled ? cfg.disabled_fg
                                      : (pressed ? cfg.primary_fg
                                                 : (hover ? cfg.primary_hover : cfg.fg_color));

        ctx.set_stroke_width(1.6);
        ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
        ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
        ctx.set_stroke_style(to_bl_rgba(arrow_col));
        ctx.stroke_path(arrowPath);
    });
}

Ttk_ElementSpec MenubuttonIndicatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ArrowElement),
    ArrowElementOptions,
    MenubuttonIndicatorGeometry,
    MenubuttonIndicatorDraw
};

} // namespace tkblend
