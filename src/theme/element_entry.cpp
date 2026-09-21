#include "element_common.h"

namespace tkblend {

struct EntryFieldElement {
    Tcl_Obj* backgroundObj;
    Tcl_Obj* bordercolorObj;
    Tcl_Obj* lightcolorObj;
    Tcl_Obj* darkcolorObj;
};

static Ttk_ElementOptionSpec EntryFieldElementOptions[] = {
    { "-background", TK_OPTION_STRING, offsetof(EntryFieldElement, backgroundObj), "" },
    { "-bordercolor", TK_OPTION_STRING, offsetof(EntryFieldElement, bordercolorObj), "" },
    { "-lightcolor", TK_OPTION_STRING, offsetof(EntryFieldElement, lightcolorObj), "" },
    { "-darkcolor", TK_OPTION_STRING, offsetof(EntryFieldElement, darkcolorObj), "" },
    { nullptr, TK_OPTION_BOOLEAN, 0, nullptr }
};

static void EntryFieldElementGeometry(
    void* /*clientData*/, void* /*elementRecord*/, Tk_Window /*tkwin*/,
    int* widthPtr, int* heightPtr, Ttk_Padding* paddingPtr
) {
    if (widthPtr)  *widthPtr  = 80;
    if (heightPtr) *heightPtr = 30;
    if (paddingPtr) {
        paddingPtr->left   = 10;
        paddingPtr->top    = 7;
        paddingPtr->right  = 10;
        paddingPtr->bottom = 7;
    }
}

static void EntryFieldElementDraw(
    void* /*clientData*/, void* /*elementRecord*/,
    Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state
) {
    const auto& cfg = ThemeEngine::instance().config();

    RenderElement(tkwin, d, b, [&](BLContext& ctx, int w, int h) {
        if (w <= 0 || h <= 0) return;

        double r = cfg.entry_radius;
        if (r * 2.0 > w) r = w / 2.0;
        if (r * 2.0 > h) r = h / 2.0;

        bool disabled = is_disabled(state);
        bool focus    = is_focus(state);
        bool readonly = is_readonly(state);
        bool hover    = is_active(state);

        uint32_t bg_col;
        uint32_t border_col;

        if (disabled) {
            bg_col = cfg.disabled_bg;
            border_col = cfg.card_border;
        } else if (readonly) {
            bg_col = cfg.card_bg;
            border_col = hover ? cfg.primary_hover : cfg.input_border;
        } else {
            bg_col = cfg.input_bg;
            border_col = focus ? cfg.input_focus_border : (hover ? blend_colors(cfg.input_border, 0xFFFFFFFF, 0.2f) : cfg.input_border);
        }

        BLPath fieldPath;
        double pad = 1.0;
        fieldPath.add_round_rect(BLRoundRect(pad, pad, w - (pad * 2.0), h - (pad * 2.0), r, r));

        // Fill background
        ctx.set_fill_style(to_bl_rgba(bg_col));
        ctx.fill_path(fieldPath);

        // Stroke border
        ctx.set_stroke_width(1.0);
        ctx.set_stroke_style(to_bl_rgba(border_col));
        ctx.stroke_path(fieldPath);

        // Focus glow halo
        if (focus && !disabled) {
            BLPath focusPath;
            focusPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r + 0.5, r + 0.5));
            ctx.set_stroke_width(cfg.focus_ring_width);
            ctx.set_stroke_style(to_bl_rgba(cfg.focus_ring_color));
            ctx.stroke_path(focusPath);
        }
    });
}

Ttk_ElementSpec EntryFieldElementSpec = {
    TTK_LAYOUT_SPEC_VERSION,
    sizeof(EntryFieldElement),
    EntryFieldElementOptions,
    EntryFieldElementGeometry,
    EntryFieldElementDraw
};

} // namespace tkblend
