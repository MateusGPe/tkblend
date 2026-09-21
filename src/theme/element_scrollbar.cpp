#include "element_common.h"

namespace tkblend {

struct ScrollbarElement {
  Tcl_Obj *backgroundObj;
  Tcl_Obj *troughColorObj;
};

static Ttk_ElementOptionSpec ScrollbarOptions[] = {
    {"-background", TK_OPTION_STRING, offsetof(ScrollbarElement, backgroundObj),
     ""},
    {"-troughcolor", TK_OPTION_STRING,
     offsetof(ScrollbarElement, troughColorObj), ""},
    {nullptr, TK_OPTION_BOOLEAN, 0, nullptr}};

static void ScrollbarTroughGeometry(void * /*clientData*/,
                                    void * /*elementRecord*/,
                                    Tk_Window /*tkwin*/, int *widthPtr,
                                    int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)   *widthPtr  = 12;
  if (heightPtr)  *heightPtr = 12;
  if (paddingPtr) *paddingPtr = {1, 1, 1, 1};
}

static void ScrollbarTroughDraw(void * /*clientData*/, void * /*elementRecord*/,
                                Tk_Window tkwin, Drawable d, Ttk_Box b,
                                Ttk_State /*state*/
) {
  const auto &cfg = ThemeEngine::instance().config();

  RenderElement(tkwin, d, b, [&](BLContext &ctx, int w, int h) {
    if (w <= 0 || h <= 0)
      return;
    BLPath troughPath;
    double r = (w < h) ? (w / 2.0) : (h / 2.0);
    troughPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));
    ctx.set_fill_style(to_bl_rgba(cfg.track_bg));
    ctx.fill_path(troughPath);
  });
}

Ttk_ElementSpec ScrollbarTroughElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, sizeof(ScrollbarElement), ScrollbarOptions,
    ScrollbarTroughGeometry, ScrollbarTroughDraw};

static void ScrollbarThumbGeometry(void * /*clientData*/,
                                   void * /*elementRecord*/,
                                   Tk_Window /*tkwin*/, int *widthPtr,
                                   int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)   *widthPtr  = 30;
  if (heightPtr)  *heightPtr = 12;
  if (paddingPtr) *paddingPtr = {0, 0, 0, 0};
}

static void ScrollbarThumbDraw(void * /*clientData*/, void * /*elementRecord*/,
                               Tk_Window tkwin, Drawable d, Ttk_Box b,
                               Ttk_State state) {
  const auto &cfg = ThemeEngine::instance().config();

  RenderElement(tkwin, d, b, [&](BLContext &ctx, int w, int h) {
    if (w <= 0 || h <= 0)
      return;

    bool pressed = is_pressed(state);
    bool hover = is_active(state);
    bool disabled = is_disabled(state);

    uint32_t thumb_col;
    if (disabled) {
      thumb_col = cfg.disabled_fg;
    } else if (pressed) {
      thumb_col = cfg.thumb_active;
    } else if (hover) {
      thumb_col = cfg.thumb_hover;
    } else {
      thumb_col = cfg.thumb_color;
    }

    double pad = (hover || pressed) ? 1.0 : 2.0;
    double pill_w = w - (pad * 2.0);
    double pill_h = h - (pad * 2.0);
    if (pill_w <= 1.0 || pill_h <= 1.0)
      return;

    double r = (pill_w < pill_h) ? (pill_w / 2.0) : (pill_h / 2.0);

    BLPath thumbPath;
    thumbPath.add_round_rect(BLRoundRect(pad, pad, pill_w, pill_h, r, r));

    // Smooth modern fill with subtle gradient for depth
    BLGradient grad;
    if (w >= h) {
      grad = BLGradient(BLLinearGradientValues(0, pad, 0, pad + pill_h));
    } else {
      grad = BLGradient(BLLinearGradientValues(pad, 0, pad + pill_w, 0));
    }
    grad.add_stop(0.0,
                  to_bl_rgba(blend_colors(thumb_col, 0xFFFFFFFF,
                                          (hover || pressed) ? 0.12f : 0.05f)));
    grad.add_stop(1.0, to_bl_rgba(thumb_col));

    ctx.set_fill_style(grad);
    ctx.fill_path(thumbPath);

    if (hover || pressed) {
      ctx.set_stroke_width(1.0);
      ctx.set_stroke_style(
          to_bl_rgba(blend_colors(thumb_col, 0xFFFFFFFF, 0.25f)));
      ctx.stroke_path(thumbPath);
    }
  });
}

Ttk_ElementSpec ScrollbarThumbElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, sizeof(ScrollbarElement), ScrollbarOptions,
    ScrollbarThumbGeometry, ScrollbarThumbDraw};

} // namespace tkblend
