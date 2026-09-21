#include "element_common.h"

namespace tkblend {

// ============================================================================
// Treeitem Indicator Element (Chevron Arrow)
// ============================================================================

struct TreeitemIndicatorElement {
    Tcl_Obj* colorObj;
    Tcl_Obj* marginsObj;
};

static Ttk_ElementOptionSpec TreeitemIndicatorOptions[] = {
    { "-indicatorcolor",   TK_OPTION_STRING, offsetof(TreeitemIndicatorElement, colorObj),   "" },
    { "-indicatormargins", TK_OPTION_STRING, offsetof(TreeitemIndicatorElement, marginsObj), "2 2 2 2" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void TreeitemIndicatorGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 16;
    if (heightPtr) *heightPtr = 16;
    if (paddingPtr) {
        paddingPtr->left   = 2;
        paddingPtr->top    = 2;
        paddingPtr->right  = 4;
        paddingPtr->bottom = 2;
    }
}

static void TreeitemIndicatorDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    // If this node is a leaf, do not draw an indicator
    if (is_leaf(state)) return;

    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        bool opened   = is_open(state);
        bool hover    = is_active(state);
        bool selected = is_selected(state);
        bool disabled = is_disabled(state);

        double cx = w / 2.0;
        double cy = h / 2.0;
        double sz = 3.5;

        // Draw hover pill behind chevron
        if (!disabled && hover) {
            BLPath hoverPill;
            double pad = 1.0;
            hoverPill.add_round_rect(BLRoundRect(pad, pad, w - pad * 2.0, h - pad * 2.0, 3.0, 3.0));
            uint32_t hover_bg = blend_colors(cfg.card_border, cfg.primary_color, 0.25f);
            ctx.set_fill_style(to_bl_rgba(hover_bg));
            ctx.fill_path(hoverPill);
        }

        BLPath arrowPath;
        if (opened) {
            // Downward-pointing chevron: \/
            arrowPath.move_to(cx - sz, cy - sz * 0.4);
            arrowPath.line_to(cx, cy + sz * 0.5);
            arrowPath.line_to(cx + sz, cy - sz * 0.4);
        } else {
            // Rightward-pointing chevron: >
            arrowPath.move_to(cx - sz * 0.4, cy - sz);
            arrowPath.line_to(cx + sz * 0.5, cy);
            arrowPath.line_to(cx - sz * 0.4, cy + sz);
        }

        uint32_t arrow_col;
        if (disabled) {
            arrow_col = cfg.disabled_fg;
        } else if (selected) {
            arrow_col = cfg.primary_fg;
        } else if (hover) {
            arrow_col = cfg.primary_hover;
        } else {
            arrow_col = blend_colors(cfg.card_border, cfg.fg_color, 0.70f);
        }

        ctx.set_stroke_width(1.6);
        ctx.set_stroke_caps(BL_STROKE_CAP_ROUND);
        ctx.set_stroke_join(BL_STROKE_JOIN_ROUND);
        ctx.set_stroke_style(to_bl_rgba(arrow_col));
        ctx.stroke_path(arrowPath);
    });
}

Ttk_ElementSpec TreeitemIndicatorElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(TreeitemIndicatorElement),
    TreeitemIndicatorOptions,
    TreeitemIndicatorGeometry,
    TreeitemIndicatorDraw
};

} // namespace tkblend
