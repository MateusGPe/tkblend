#pragma once

#include "platform_compat.h"
#include <cstdint>
#include <cstddef>

namespace tkblend {

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
