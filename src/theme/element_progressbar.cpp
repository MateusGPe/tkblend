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
    if (widthPtr)  *widthPtr  = 140;
    if (heightPtr) *heightPtr = 12;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 2;
        paddingPtr->bottom = 2;
    }
}

static void PbarTroughDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        double r = (w < h) ? std::min(w / 2.0, 6.0) : (h / 2.0);

        BLPath troughPath;
        troughPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

        // Dark track background
        ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
        ctx.fill_path(troughPath);

        // Crisp border
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
    if (widthPtr)  *widthPtr  = 16;
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
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 1 || h <= 1) return;

        // Pre-fill with trough track color so bar edges blend seamlessly inside the trough
        ctx.fill_all(to_bl_rgba(cfg.track_bg));

        double r = std::min(w / 2.0, h / 2.0);

        BLPath barPath;
        barPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

        BLGradient grad;
        if (w >= h) {
            grad = BLGradient(BLLinearGradientValues(0, 0, w, 0));
        } else {
            grad = BLGradient(BLLinearGradientValues(0, h, 0, 0));
        }
        grad.add_stop(0.0, to_bl_rgba(cfg.primary_color));
        grad.add_stop(1.0, to_bl_rgba(cfg.primary_hover));

        ctx.set_fill_style(grad);
        ctx.fill_path(barPath);

        // Specular highlight along the leading edge
        auto draw_specular = [&](double x1, double y1, double x2, double y2) {
            BLPath hiPath;
            hiPath.move_to(x1, y1);
            hiPath.line_to(x2, y2);
            ctx.set_stroke_width(1.0);
            ctx.set_stroke_style(to_bl_rgba(0x40FFFFFF));
            ctx.stroke_path(hiPath);
        };
        if (w >= h && h >= 6 && w > 12) {
            draw_specular(r * 0.6, 1.5, w - r * 0.6, 1.5);
        } else if (w < h && w >= 6 && h > 12) {
            draw_specular(1.5, r * 0.6, 1.5, h - r * 0.6);
        }
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
