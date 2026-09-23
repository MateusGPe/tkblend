#pragma once

#include <blend2d.h>
#include <cstdint>
#include <string>

namespace tkblend {

// Color representation (RGBA 32-bit unpacked)
struct Color {
    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    uint8_t a = 255;

    constexpr Color() = default;
    constexpr Color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255)
        : r(r), g(g), b(b), a(a) {}

    static Color from_hex(const std::string& hex);
    static Color from_u32(uint32_t argb);
    uint32_t to_u32() const;
    BLRgba32 to_bl_rgba32() const;

    // Fast Color Math
    Color lighten(double factor) const;
    Color darken(double factor) const;
    Color lerp(const Color& other, double t) const;
    Color with_alpha(uint8_t new_a) const;
    Color with_alpha_f(double new_a) const;
};

} // namespace tkblend
