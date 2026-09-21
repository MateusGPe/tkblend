#pragma once

#include "theme_engine.h"
#include "../blit/blit_backend.h"
#include <blend2d.h>
#include <cmath>
#include <functional>

namespace tkblend {

inline BLRgba32 to_bl_rgba(uint32_t argb) {
    uint8_t a = static_cast<uint8_t>((argb >> 24) & 0xFF);
    uint8_t r = static_cast<uint8_t>((argb >> 16) & 0xFF);
    uint8_t g = static_cast<uint8_t>((argb >> 8) & 0xFF);
    uint8_t b = static_cast<uint8_t>(argb & 0xFF);
    return BLRgba32(r, g, b, a);
}

inline uint32_t blend_colors(uint32_t c1, uint32_t c2, float t) {
    if (t <= 0.0f) return c1;
    if (t >= 1.0f) return c2;
    float inv = 1.0f - t;
    uint32_t a = static_cast<uint32_t>(((c1 >> 24) & 0xFF) * inv + ((c2 >> 24) & 0xFF) * t);
    uint32_t r = static_cast<uint32_t>(((c1 >> 16) & 0xFF) * inv + ((c2 >> 16) & 0xFF) * t);
    uint32_t g = static_cast<uint32_t>(((c1 >> 8) & 0xFF) * inv + ((c2 >> 8) & 0xFF) * t);
    uint32_t b = static_cast<uint32_t>((c1 & 0xFF) * inv + (c2 & 0xFF) * t);
    return (a << 24) | (r << 16) | (g << 8) | b;
}

inline bool is_disabled(Ttk_State state) { return (state & TTK_STATE_DISABLED) != 0; }
inline bool is_pressed(Ttk_State state)  { return (state & TTK_STATE_PRESSED) != 0; }
inline bool is_active(Ttk_State state)   { return (state & TTK_STATE_ACTIVE) != 0; }
inline bool is_focus(Ttk_State state)    { return (state & TTK_STATE_FOCUS) != 0; }
inline bool is_selected(Ttk_State state) { return (state & TTK_STATE_SELECTED) != 0; }
inline bool is_readonly(Ttk_State state) { return (state & TTK_STATE_READONLY) != 0; }
inline bool is_alternate(Ttk_State state) { return (state & TTK_STATE_ALTERNATE) != 0; }

#ifndef TTK_STATE_OPEN
#define TTK_STATE_OPEN (1<<16)
#endif
#ifndef TTK_STATE_LEAF
#define TTK_STATE_LEAF (1<<17)
#endif

inline bool is_open(Ttk_State state) { return (state & TTK_STATE_OPEN) != 0; }
inline bool is_leaf(Ttk_State state) { return (state & TTK_STATE_LEAF) != 0; }

// Safe template wrapper for drawing an element into Blend2D and blitting zero-copy
template<typename RenderFn>
inline void RenderElement(Tk_Window tkwin, Drawable d, Ttk_Box b, RenderFn&& render_fn) {
    if (!tkwin || d == None) return;
    if (b.width <= 0 || b.height <= 0) return;

    BLImage img;
    if (img.create(b.width, b.height, BL_FORMAT_PRGB32) != BL_SUCCESS) return;

    BLContext ctx;
    if (ctx.begin(img) != BL_SUCCESS) return;
    ctx.set_comp_op(BL_COMP_OP_SRC_OVER);

    // Pre-fill background with resolved container background to prevent
    // non-alpha blitting black box artifacts on X11 / Win32
    uint32_t bg_color = ThemeEngine::instance().config().bg_color;
    uint32_t resolved_bg = ResolveAncestorBackground(tkwin, bg_color);
    ctx.fill_all(to_bl_rgba(resolved_bg));

    // Execute user render callback
    render_fn(ctx, b.width, b.height);

    ctx.end();

    BLImageData imgData;
    if (img.get_data(&imgData) == BL_SUCCESS) {
        NativeBlit(
            tkwin,
            d,
            b,
            static_cast<const uint8_t*>(imgData.pixel_data),
            static_cast<size_t>(imgData.stride),
            b.width,
            b.height
        );
    }
}

// Forward declarations of Element Specs
extern Ttk_ElementSpec ButtonElementSpec;
extern Ttk_ElementSpec EntryFieldElementSpec;
extern Ttk_ElementSpec CheckIndicatorElementSpec;
extern Ttk_ElementSpec RadioIndicatorElementSpec;
extern Ttk_ElementSpec SwitchIndicatorElementSpec;
extern Ttk_ElementSpec PbarTroughElementSpec;
extern Ttk_ElementSpec PbarBarElementSpec;
extern Ttk_ElementSpec ScrollbarTroughElementSpec;
extern Ttk_ElementSpec ScrollbarThumbElementSpec;
extern Ttk_ElementSpec ScaleTroughElementSpec;
extern Ttk_ElementSpec ScaleSliderElementSpec;
extern Ttk_ElementSpec ComboboxDownArrowElementSpec;
extern Ttk_ElementSpec SpinboxUpArrowElementSpec;
extern Ttk_ElementSpec SpinboxDownArrowElementSpec;
extern Ttk_ElementSpec SpinboxButtonsElementSpec;
extern Ttk_ElementSpec MenubuttonIndicatorElementSpec;
extern Ttk_ElementSpec NotebookTabElementSpec;
extern Ttk_ElementSpec NotebookClientElementSpec;
extern Ttk_ElementSpec LabelframeBorderElementSpec;
extern Ttk_ElementSpec SeparatorElementSpec;
extern Ttk_ElementSpec HorizontalSeparatorElementSpec;
extern Ttk_ElementSpec VerticalSeparatorElementSpec;
extern Ttk_ElementSpec SizegripElementSpec;
extern Ttk_ElementSpec SashElementSpec;
extern Ttk_ElementSpec HorizontalSashElementSpec;
extern Ttk_ElementSpec VerticalSashElementSpec;
extern Ttk_ElementSpec TreeitemIndicatorElementSpec;

} // namespace tkblend
