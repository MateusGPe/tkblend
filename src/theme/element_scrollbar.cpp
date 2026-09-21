#include "element_common.h"

namespace tkblend {

struct ScrollbarElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* troughColorObj;
};

static Ttk_ElementOptionSpec ScrollbarOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ScrollbarElement, backgroundObj), "" },
    { "-troughcolor", TK_OPTION_STRING, offsetof(ScrollbarElement, troughColorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void ScrollbarTroughGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 12;
    if (heightPtr) *heightPtr = 12;
    if (paddingPtr) {
        paddingPtr->left   = 1;
        paddingPtr->top    = 1;
        paddingPtr->right  = 1;
        paddingPtr->bottom = 1;
    }
}

static void ScrollbarTroughDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        BLPath troughPath;
        double r = cfg.scrollbar_radius;
        troughPath.add_round_rect(BLRoundRect(0, 0, w, h, r, r));
        ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
        ctx.fill_path(troughPath);
    });
}

Ttk_ElementSpec ScrollbarTroughElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ScrollbarElement),
    ScrollbarOptions,
    ScrollbarTroughGeometry,
    ScrollbarTroughDraw
};

static void ScrollbarThumbGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 24;
    if (heightPtr) *heightPtr = 10;
    if (paddingPtr) {
        paddingPtr->left   = 1;
        paddingPtr->top    = 1;
        paddingPtr->right  = 1;
        paddingPtr->bottom = 1;
    }
}

static void ScrollbarThumbDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        bool pressed = is_pressed(state);
        bool hover   = is_active(state);

        uint32_t thumb_col = pressed ? cfg.thumb_active : (hover ? cfg.thumb_hover : cfg.thumb_color);

        double pad = hover ? 1.0 : 2.0;
        double pill_w = w - (pad * 2.0);
        double pill_h = h - (pad * 2.0);
        if (pill_w <= 0.0 || pill_h <= 0.0) return;

        double r = (pill_w < pill_h) ? (pill_w / 2.0) : (pill_h / 2.0);
        if (r > cfg.scrollbar_radius) r = cfg.scrollbar_radius;

        BLPath thumbPath;
        thumbPath.add_round_rect(BLRoundRect(pad, pad, pill_w, pill_h, r, r));

        ctx.set_fill_style(to_bl_rgba(thumb_col));
        ctx.fill_path(thumbPath);
    });
}

Ttk_ElementSpec ScrollbarThumbElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ScrollbarElement),
    ScrollbarOptions,
    ScrollbarThumbGeometry,
    ScrollbarThumbDraw
};

} // namespace tkblend
