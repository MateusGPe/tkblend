#include "element_common.h"

namespace tkblend {

struct ScaleElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* troughColorObj;
};

static Ttk_ElementOptionSpec ScaleOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(ScaleElement, backgroundObj), "" },
    { "-troughcolor", TK_OPTION_STRING, offsetof(ScaleElement, troughColorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void ScaleTroughGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 120;
    if (heightPtr) *heightPtr = 20;
    if (paddingPtr) {
        paddingPtr->left   = 0;
        paddingPtr->top    = 0;
        paddingPtr->right  = 0;
        paddingPtr->bottom = 0;
    }
}

static void ScaleTroughDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool is_horiz = (w >= h);
        double track_size = 6.0;
        double radius = track_size / 2.0;

        BLPath trackPath;
        if (is_horiz) {
            double thumb_radius = h / 2.0;
            double track_x = (w > 2.0 * thumb_radius) ? thumb_radius : 1.0;
            double track_w = (w > 2.0 * thumb_radius) ? (w - 2.0 * thumb_radius) : (w - 2.0);
            double ty = (h - track_size) / 2.0;
            trackPath.add_round_rect(BLRoundRect(track_x, ty, track_w, track_size, radius, radius));
        } else {
            double thumb_radius = w / 2.0;
            double track_y = (h > 2.0 * thumb_radius) ? thumb_radius : 1.0;
            double track_h = (h > 2.0 * thumb_radius) ? (h - 2.0 * thumb_radius) : (h - 2.0);
            double tx = (w - track_size) / 2.0;
            trackPath.add_round_rect(BLRoundRect(tx, track_y, track_size, track_h, radius, radius));
        }

        // Production track styling
        ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
        ctx.fill_path(trackPath);

        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.input_border));
        ctx.stroke_path(trackPath);
    });
}

Ttk_ElementSpec ScaleTroughElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ScaleElement),
    ScaleOptions,
    ScaleTroughGeometry,
    ScaleTroughDraw
};

static void ScaleSliderGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 20;
    if (heightPtr) *heightPtr = 20;
    if (paddingPtr) {
        paddingPtr->left   = 0;
        paddingPtr->top    = 0;
        paddingPtr->right  = 0;
        paddingPtr->bottom = 0;
    }
}

static void ScaleSliderDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool is_horiz = (w >= h);
        double track_size = 6.0;

        // Draw track segment through slider area
        BLPath trackSegment;
        if (is_horiz) {
            double ty = (h - track_size) / 2.0;
            trackSegment.add_rect(BLRect(0.0, ty, w, track_size));
        } else {
            double tx = (w - track_size) / 2.0;
            trackSegment.add_rect(BLRect(tx, 0.0, track_size, h));
        }
        ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
        ctx.fill_path(trackSegment);

        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(cfg.input_border));
        ctx.stroke_path(trackSegment);

        bool disabled = is_disabled(state);
        bool pressed  = is_pressed(state);
        bool hover    = is_active(state);

        double cx = w / 2.0;
        double cy = h / 2.0;
        double r = std::min(w, h) / 2.0 - 2.5;
        if (r < 3.0) r = 3.0;

        // Modern flat thumb circle
        BLCircle thumbCircle(cx, cy, r);
        uint32_t fill_color = disabled ? cfg.disabled_bg : (pressed ? cfg.primary_active : (hover ? cfg.primary_hover : cfg.primary_color));
        uint32_t border_color = disabled ? cfg.card_border : 0xFFFFFFFF;

        ctx.set_fill_style(to_bl_rgba(fill_color));
        ctx.fill_circle(thumbCircle);

        ctx.set_stroke_width(2.0);
        ctx.set_stroke_style(to_bl_rgba(border_color));
        ctx.stroke_circle(thumbCircle);

        // Crisp inner dot
        BLCircle innerDot(cx, cy, r * 0.35);
        ctx.set_fill_style(to_bl_rgba(disabled ? cfg.disabled_fg : 0xFFFFFFFF));
        ctx.fill_circle(innerDot);
    });
}

Ttk_ElementSpec ScaleSliderElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(ScaleElement),
    ScaleOptions,
    ScaleSliderGeometry,
    ScaleSliderDraw
};

} // namespace tkblend
