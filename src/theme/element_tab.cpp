#include "element_common.h"

namespace tkblend {

struct TabElement {
  Tcl_Obj *backgroundObj;
  Tcl_Obj *bordercolorObj;
  Tcl_Obj *lightcolorObj;
  Tcl_Obj *darkcolorObj;
};

static Ttk_ElementOptionSpec TabElementOptions[] = {
    {"-background", TK_OPTION_STRING, offsetof(TabElement, backgroundObj), ""},
    {"-bordercolor", TK_OPTION_STRING, offsetof(TabElement, bordercolorObj),
     ""},
    {"-lightcolor", TK_OPTION_STRING, offsetof(TabElement, lightcolorObj), ""},
    {"-darkcolor", TK_OPTION_STRING, offsetof(TabElement, darkcolorObj), ""},
    {nullptr, TK_OPTION_BOOLEAN, 0, nullptr}};

// ============================================================================
// Notebook Tab Element
// ============================================================================
static void NotebookTabGeometry(void * /*clientData*/, void * /*elementRecord*/,
                                Tk_Window /*tkwin*/, int *widthPtr,
                                int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)
    *widthPtr = 60;
  if (heightPtr)
    *heightPtr = 32;
  if (paddingPtr) {
    paddingPtr->left = 16;
    paddingPtr->top = 7;
    paddingPtr->right = 16;
    paddingPtr->bottom = 7;
  }
}

static void NotebookTabDraw(void * /*clientData*/, void * /*elementRecord*/,
                            Tk_Window tkwin, Drawable d, Ttk_Box b,
                            Ttk_State state) {
  const auto &cfg = ThemeEngine::instance().config();

  RenderElement(tkwin, d, b, [&](BLContext &ctx, int w, int h) {
    if (w <= 0 || h <= 0)
      return;

    bool selected = is_selected(state);
    bool disabled = is_disabled(state);
    bool hover = is_active(state);

    double r = 6.0;
    double pad = 1.0;
    BLPath tabPath;
    tabPath.add_round_rect(
        BLRoundRect(pad, pad, w - pad * 2.0, h - pad * 2.0, r, r));

    uint32_t fill_col;
    uint32_t border_col;

    if (disabled) {
      fill_col = cfg.disabled_bg;
      border_col = cfg.card_border;
    } else if (selected) {
      fill_col = cfg.primary_color;
      border_col = cfg.primary_hover;
    } else if (hover) {
      fill_col = cfg.secondary_hover;
      border_col = cfg.input_border;
    } else {
      fill_col = blend_colors(cfg.bg_color, cfg.card_bg, 0.6f);
      border_col = cfg.card_border;
    }

    // Fill tab surface
    if (selected) {
      // Subtle gradient for selected tab
      BLGradient grad(BLLinearGradientValues(0, 0, 0, h));
      grad.add_stop(0.0, to_bl_rgba(blend_colors(fill_col, 0xFFFFFFFF, 0.1f)));
      grad.add_stop(1.0, to_bl_rgba(fill_col));
      ctx.set_fill_style(grad);
    } else {
      ctx.set_fill_style(to_bl_rgba(fill_col));
    }
    ctx.fill_path(tabPath);

    // Stroke border
    ctx.set_stroke_width(1.0);
    ctx.set_stroke_style(to_bl_rgba(border_col));
    ctx.stroke_path(tabPath);

    // Top specular highlight on selected tab
    if (selected && h > 10) {
      BLPath hiPath;
      hiPath.move_to(r + 2.0, 2.0);
      hiPath.line_to(w - r - 2.0, 2.0);
      ctx.set_stroke_width(1.0);
      ctx.set_stroke_style(to_bl_rgba(0x40FFFFFF));
      ctx.stroke_path(hiPath);
    }
  });
}

Ttk_ElementSpec NotebookTabElementSpec = {TTK_LAYOUT_SPEC_VERSION,
                                          sizeof(TabElement), TabElementOptions,
                                          NotebookTabGeometry, NotebookTabDraw};

// ============================================================================
// Notebook Client Area (Container) Element
// ============================================================================
struct NotebookClientElement {
  Tcl_Obj *backgroundObj;
  Tcl_Obj *bordercolorObj;
};

static Ttk_ElementOptionSpec NotebookClientOptions[] = {
    {"-background", TK_OPTION_STRING,
     offsetof(NotebookClientElement, backgroundObj), ""},
    {"-bordercolor", TK_OPTION_STRING,
     offsetof(NotebookClientElement, bordercolorObj), ""},
    {nullptr, TK_OPTION_BOOLEAN, 0, nullptr}};

static void NotebookClientGeometry(void * /*clientData*/,
                                   void * /*elementRecord*/,
                                   Tk_Window /*tkwin*/, int *widthPtr,
                                   int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)
    *widthPtr = 0;
  if (heightPtr)
    *heightPtr = 0;
  if (paddingPtr) {
    paddingPtr->left = 2;
    paddingPtr->top = 2;
    paddingPtr->right = 2;
    paddingPtr->bottom = 2;
  }
}

static void NotebookClientDraw(void * /*clientData*/, void * /*elementRecord*/,
                               Tk_Window tkwin, Drawable d, Ttk_Box b,
                               Ttk_State /*state*/) {
  const auto &cfg = ThemeEngine::instance().config();

  RenderElement(tkwin, d, b, [&](BLContext &ctx, int w, int h) {
    if (w <= 0 || h <= 0)
      return;

    double r = 8.0;
    BLPath clientPath;
    clientPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

    // Fill card background
    ctx.set_fill_style(to_bl_rgba(cfg.card_bg));
    ctx.fill_path(clientPath);

    // Stroke modern card border
    ctx.set_stroke_width(1.0);
    ctx.set_stroke_style(to_bl_rgba(cfg.card_border));
    ctx.stroke_path(clientPath);
  });
}

Ttk_ElementSpec NotebookClientElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, sizeof(NotebookClientElement),
    NotebookClientOptions, NotebookClientGeometry, NotebookClientDraw};

// ============================================================================
// Labelframe Card Border Element
// ============================================================================
struct LabelframeBorderElement {
  Tcl_Obj *backgroundObj;
  Tcl_Obj *bordercolorObj;
};

static Ttk_ElementOptionSpec LabelframeBorderOptions[] = {
    {"-background", TK_OPTION_STRING,
     offsetof(LabelframeBorderElement, backgroundObj), ""},
    {"-bordercolor", TK_OPTION_STRING,
     offsetof(LabelframeBorderElement, bordercolorObj), ""},
    {nullptr, TK_OPTION_BOOLEAN, 0, nullptr}};

static void LabelframeBorderGeometry(void * /*clientData*/,
                                     void * /*elementRecord*/,
                                     Tk_Window /*tkwin*/, int *widthPtr,
                                     int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)
    *widthPtr = 0;
  if (heightPtr)
    *heightPtr = 0;
  if (paddingPtr) {
    paddingPtr->left = 14;
    paddingPtr->top = 14;
    paddingPtr->right = 14;
    paddingPtr->bottom = 14;
  }
}

static void LabelframeBorderDraw(void * /*clientData*/,
                                 void * /*elementRecord*/, Tk_Window tkwin,
                                 Drawable d, Ttk_Box b, Ttk_State /*state*/
) {
  const auto &cfg = ThemeEngine::instance().config();

  RenderElement(tkwin, d, b, [&](BLContext &ctx, int w, int h) {
    if (w <= 0 || h <= 0)
      return;

    double r = 8.0;
    BLPath cardPath;
    cardPath.add_round_rect(BLRoundRect(0.5, 0.5, w - 1.0, h - 1.0, r, r));

    // Fill card background
    ctx.set_fill_style(to_bl_rgba(cfg.card_bg));
    ctx.fill_path(cardPath);

    // Stroke modern card border
    ctx.set_stroke_width(1.0);
    ctx.set_stroke_style(to_bl_rgba(cfg.card_border));
    ctx.stroke_path(cardPath);
  });
}

Ttk_ElementSpec LabelframeBorderElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, sizeof(LabelframeBorderElement),
    LabelframeBorderOptions, LabelframeBorderGeometry, LabelframeBorderDraw};

// ============================================================================
// Frame Border Element (Solid container / card background filling)
// ============================================================================
struct FrameBorderElement {
  Tcl_Obj *backgroundObj;
};

static Ttk_ElementOptionSpec FrameBorderOptions[] = {
    {"-background", TK_OPTION_STRING,
     offsetof(FrameBorderElement, backgroundObj), ""},
    {nullptr, TK_OPTION_BOOLEAN, 0, nullptr}};

static void FrameBorderGeometry(void * /*clientData*/, void * /*elementRecord*/,
                                Tk_Window /*tkwin*/, int *widthPtr,
                                int *heightPtr, Ttk_Padding *paddingPtr) {
  if (widthPtr)
    *widthPtr = 0;
  if (heightPtr)
    *heightPtr = 0;
  if (paddingPtr) {
    paddingPtr->left = 0;
    paddingPtr->top = 0;
    paddingPtr->right = 0;
    paddingPtr->bottom = 0;
  }
}

static void FrameBorderDraw(void * /*clientData*/, void *elementRecord,
                            Tk_Window tkwin, Drawable d, Ttk_Box b,
                            Ttk_State /*state*/
) {
  auto *el = static_cast<FrameBorderElement *>(elementRecord);
  uint32_t fill_color = 0;
  if (el && el->backgroundObj) {
    const char *bg_str = Tcl_GetString(el->backgroundObj);
    if (bg_str && bg_str[0] != '\0') {
      parse_hex_color(bg_str, fill_color);
    }
  }

  RenderElement(
      tkwin, d, b,
      [&](BLContext & /*ctx*/, int /*w*/, int /*h*/) {
        // Base container fill is automatically performed by RenderElement
      },
      fill_color);
}

Ttk_ElementSpec FrameBorderElementSpec = {
    TTK_LAYOUT_SPEC_VERSION, sizeof(FrameBorderElement), FrameBorderOptions,
    FrameBorderGeometry, FrameBorderDraw};

} // namespace tkblend
