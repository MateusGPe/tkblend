#include "element_common.h"

namespace tkblend {

struct ProgressBarElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* pbarColorObj;
};

static Ttk_ElementOptionSpec ProgressBarOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ProgressBarElement, backgroundObj), "" },
    { "-pbarcolor", TK_OPTION_STRING, offsetof(ProgressBarElement, pbarColorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void PbarTroughGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 120;
    if (heightPtr) *heightPtr = 10;
    if (paddingPtr) {
        paddingPtr->left   = 1;
        paddingPtr->top    = 1;
        paddingPtr->right  = 1;
        paddingPtr->bottom = 1;
    }
}

static void PbarTroughDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        double r = cfg.pbar_radius;
        if (r * 2.0 > w) r = w / 2.0;
        if (r * 2.0 > h) r = h / 2.0;

        BLPath troughPath;
        troughPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

        ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
        ctx.fill_path(troughPath);
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.input_border));
        ctx.stroke_path(troughPath);
    });
}

Ttk_ElementSpec PbarTroughElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ProgressBarElement),
    ProgressBarOptions,
    PbarTroughGeometry,
    PbarTroughDraw
};

static void PbarBarGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 10;
    if (heightPtr) *heightPtr = 8;
    if (paddingPtr) {
        paddingPtr->left   = 0;
        paddingPtr->top    = 0;
        paddingPtr->right  = 0;
        paddingPtr->bottom = 0;
    }
}

static void PbarBarDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        double r = cfg.pbar_radius;
        if (r * 2.0 > w) r = w / 2.0;
        if (r * 2.0 > h) r = h / 2.0;

        BLPath barPath;
        barPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

        BLGradient grad;
        if (w >= h) {
            // Horizontal bar gradient
            grad = BLGradient(BLLinearGradientValues(0, 0, w, 0));
        } else {
            // Vertical bar gradient
            grad = BLGradient(BLLinearGradientValues(0, h, 0, 0));
        }
        grad.add_stop(0.0, to_bl_rgba(cfg.primary_color));
        grad.add_stop(1.0, to_bl_rgba(cfg.primary_hover));

        ctx.set_fill_style(grad);
        ctx.fill_path(barPath);
    });
}

Ttk_ElementSpec PbarBarElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ProgressBarElement),
    ProgressBarOptions,
    PbarBarGeometry,
    PbarBarDraw
};

} // namespace tkblend
