#include "element_common.h"

namespace tkblend {

// ============================================================================
// Separator Element
// ============================================================================

struct SeparatorElement {
    Tcl_Obj* orientObj;
    Tcl_Obj* backgroundObj;
};

static Ttk_ElementOptionSpec SeparatorOptions[] = {
    { "-orient",     TK_OPTION_STRING, offsetof(SeparatorElement, orientObj), "horizontal" },
    { "-background", TK_OPTION_STRING, offsetof(SeparatorElement, backgroundObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void SeparatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 1;
    if (heightPtr) *heightPtr = 9;
    if (paddingPtr) {
        paddingPtr->left = 0; paddingPtr->top = 4; paddingPtr->right = 0; paddingPtr->bottom = 4;
    }
}

static void HorizontalSeparatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 1;
    if (heightPtr) *heightPtr = 9;
    if (paddingPtr) {
        paddingPtr->left = 0; paddingPtr->top = 4; paddingPtr->right = 0; paddingPtr->bottom = 4;
    }
}

static void VerticalSeparatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 9;
    if (heightPtr) *heightPtr = 1;
    if (paddingPtr) {
        paddingPtr->left = 4; paddingPtr->top = 0; paddingPtr->right = 4; paddingPtr->bottom = 0;
    }
}

static void HorizontalSeparatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;
        double cy = std::floor(h / 2.0) + 0.5;

        BLPath line;
        line.move_to(0.0, cy);
        line.line_to(w, cy);

        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.card_border));
        ctx.stroke_path(line);
    });
}

static void VerticalSeparatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;
        double cx = std::floor(w / 2.0) + 0.5;

        BLPath line;
        line.move_to(cx, 0.0);
        line.line_to(cx, h);

        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.card_border));
        ctx.stroke_path(line);
    });
}

static void GeneralSeparatorDraw(
    void* clientData, void* elementRecord,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    if (b.width > b.height) {
        HorizontalSeparatorDraw(clientData, elementRecord, tkwin, d, b, state);
    } else {
        VerticalSeparatorDraw(clientData, elementRecord, tkwin, d, b, state);
    }
}

Ttk_ElementSpec SeparatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SeparatorElement),
    SeparatorOptions,
    SeparatorGeometry,
    GeneralSeparatorDraw
};

Ttk_ElementSpec HorizontalSeparatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SeparatorElement),
    SeparatorOptions,
    HorizontalSeparatorGeometry,
    HorizontalSeparatorDraw
};

Ttk_ElementSpec VerticalSeparatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SeparatorElement),
    SeparatorOptions,
    VerticalSeparatorGeometry,
    VerticalSeparatorDraw
};

// ============================================================================
// Sizegrip Element
// ============================================================================

struct SizegripElement {
    Tcl_Obj* backgroundObj;
};

static Ttk_ElementOptionSpec SizegripOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(SizegripElement, backgroundObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void SizegripGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 16;
    if (heightPtr) *heightPtr = 16;
    if (paddingPtr) {
        paddingPtr->left = 0; paddingPtr->top = 0; paddingPtr->right = 0; paddingPtr->bottom = 0;
    }
}

static void SizegripDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool hover = is_active(state);
        uint32_t dot_color = hover ? cfg.primary_color
                                   : blend_colors(cfg.card_border, cfg.fg_color, 0.40f);
        ctx.set_fill_style(to_bl_rgba(dot_color));

        double r = 1.25;
        // Draw modern 3-tier diagonal grip dots in bottom-right corner
        struct Dot { double x; double y; };
        Dot dots[] = {
            { w - 4.0,  h - 4.0 },
            { w - 8.0,  h - 4.0 },
            { w - 4.0,  h - 8.0 },
            { w - 12.0, h - 4.0 },
            { w - 8.0,  h - 8.0 },
            { w - 4.0,  h - 12.0 },
        };

        for (const auto& dot : dots) {
            if (dot.x >= 0 && dot.y >= 0) {
                ctx.fill_circle(dot.x, dot.y, r);
            }
        }
    });
}

Ttk_ElementSpec SizegripElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SizegripElement),
    SizegripOptions,
    SizegripGeometry,
    SizegripDraw
};

// ============================================================================
// Panedwindow Sash Elements
// ============================================================================

struct SashElement {
    Tcl_Obj* backgroundObj;
};

static Ttk_ElementOptionSpec SashOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(SashElement, backgroundObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void HorizontalSashGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 1;
    if (heightPtr) *heightPtr = 6;
    if (paddingPtr) {
        paddingPtr->left = 0; paddingPtr->top = 1; paddingPtr->right = 0; paddingPtr->bottom = 1;
    }
}

static void VerticalSashGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 6;
    if (heightPtr) *heightPtr = 1;
    if (paddingPtr) {
        paddingPtr->left = 1; paddingPtr->top = 0; paddingPtr->right = 1; paddingPtr->bottom = 0;
    }
}

static void HorizontalSashDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool hover   = is_active(state);
        bool pressed = is_pressed(state);

        double cy = std::floor(h / 2.0) + 0.5;

        // Subtle divider hairline
        BLPath line;
        line.move_to(0.0, cy);
        line.line_to(w, cy);
        uint32_t line_col = (hover || pressed) ? cfg.primary_color : cfg.card_border;
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(line_col));
        ctx.stroke_path(line);

        // Center pill handle
        double handle_w = 32.0;
        double handle_h = 3.0;
        if (handle_w > w - 8.0) handle_w = std::max(4.0, w - 8.0);
        double hx = (w - handle_w) / 2.0;
        double hy = (h - handle_h) / 2.0;

        uint32_t handle_col = pressed ? cfg.primary_active
                                      : (hover ? cfg.primary_hover : cfg.thumb_color);
        BLPath pill;
        pill.add_round_rect(BLRoundRect(hx, hy, handle_w, handle_h, 1.5, 1.5));
        ctx.set_fill_style(to_bl_rgba(handle_col));
        ctx.fill_path(pill);
    });
}

static void VerticalSashDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool hover   = is_active(state);
        bool pressed = is_pressed(state);

        double cx = std::floor(w / 2.0) + 0.5;

        // Subtle divider hairline
        BLPath line;
        line.move_to(cx, 0.0);
        line.line_to(cx, h);
        uint32_t line_col = (hover || pressed) ? cfg.primary_color : cfg.card_border;
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(line_col));
        ctx.stroke_path(line);

        // Center pill handle
        double handle_w = 3.0;
        double handle_h = 32.0;
        if (handle_h > h - 8.0) handle_h = std::max(4.0, h - 8.0);
        double hx = (w - handle_w) / 2.0;
        double hy = (h - handle_h) / 2.0;

        uint32_t handle_col = pressed ? cfg.primary_active
                                      : (hover ? cfg.primary_hover : cfg.thumb_color);
        BLPath pill;
        pill.add_round_rect(BLRoundRect(hx, hy, handle_w, handle_h, 1.5, 1.5));
        ctx.set_fill_style(to_bl_rgba(handle_col));
        ctx.fill_path(pill);
    });
}

static void GeneralSashDraw(
    void* clientData, void* elementRecord,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    if (b.width > b.height) {
        HorizontalSashDraw(clientData, elementRecord, tkwin, d, b, state);
    } else {
        VerticalSashDraw(clientData, elementRecord, tkwin, d, b, state);
    }
}

Ttk_ElementSpec SashElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SashElement),
    SashOptions,
    HorizontalSashGeometry,
    GeneralSashDraw
};

Ttk_ElementSpec HorizontalSashElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SashElement),
    SashOptions,
    HorizontalSashGeometry,
    HorizontalSashDraw
};

Ttk_ElementSpec VerticalSashElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(SashElement),
    SashOptions,
    VerticalSashGeometry,
    VerticalSashDraw
};

} // namespace tkblend
