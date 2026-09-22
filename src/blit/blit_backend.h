#pragma once

#include "platform_compat.h"
#include <cstdint>
#include <cstddef>

namespace tkblend {

// Calculated clipping result for blitting into a window
struct BlitClipResult {
    int src_x{0};
    int src_y{0};
    int dst_x{0};
    int dst_y{0};
    int req_w{0};
    int req_h{0};
    bool visible{false};
};

// Compute 4-sided window and source clipping boundaries
BlitClipResult ComputeBlitClip(
    Tk_Window tkwin,
    const Ttk_Box& box,
    int width,
    int height
);

// Abstraction for blitting 32-bit ARGB/PRGB pixel buffer to native Tk Drawable
bool NativeBlit(
    Tk_Window tkwin,
    Drawable drawable,
    const Ttk_Box& box,
    const uint8_t* pixelData,
    size_t stride,
    int width,
    int height
);

// Traversal helper to find the effective background color of ancestor windows
// returns 32-bit 0xAARRGGBB color format
uint32_t ResolveAncestorBackground(Tk_Window tkwin, uint32_t fallback_argb = 0xFFF0F0F0);

} // namespace tkblend
