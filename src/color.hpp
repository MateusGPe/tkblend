#pragma once

#include "string_utils.hpp"
#include <blend2d.h>
#include <cstdint>
#include <string>
#include <string_view>

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

    static constexpr Color from_hex(std::string_view sv) noexcept {
        if (!sv.empty() && sv.front() == '#') {
            sv.remove_prefix(1);
        }
        switch (sv.size()) {
            case 3: // #RGB
                return Color(parse_1hex(sv[0]), parse_1hex(sv[1]), parse_1hex(sv[2]), 255);
            case 4: // #RGBA
                return Color(parse_1hex(sv[0]), parse_1hex(sv[1]), parse_1hex(sv[2]), parse_1hex(sv[3]));
            case 6: // #RRGGBB
                return Color(parse_2hex(sv[0], sv[1]), parse_2hex(sv[2], sv[3]), parse_2hex(sv[4], sv[5]), 255);
            case 8: // #RRGGBBAA
                return Color(parse_2hex(sv[0], sv[1]), parse_2hex(sv[2], sv[3]), parse_2hex(sv[4], sv[5]), parse_2hex(sv[6], sv[7]));
            default:
                return Color(0, 0, 0, 255);
        }
    }

    static Color from_hex(const std::string& hex) {
        return from_hex(std::string_view(hex));
    }

    static constexpr Color from_u32(uint32_t argb) noexcept {
        uint8_t a = static_cast<uint8_t>((argb >> 24) & 0xFF);
        uint8_t r = static_cast<uint8_t>((argb >> 16) & 0xFF);
        uint8_t g = static_cast<uint8_t>((argb >> 8) & 0xFF);
        uint8_t b = static_cast<uint8_t>(argb & 0xFF);
        return Color(r, g, b, a);
    }

    constexpr uint32_t to_u32() const noexcept {
        return (static_cast<uint32_t>(a) << 24) |
               (static_cast<uint32_t>(r) << 16) |
               (static_cast<uint32_t>(g) << 8)  |
                static_cast<uint32_t>(b);
    }

    BLRgba32 to_bl_rgba32() const noexcept;

    // Fast Color Math
    Color lighten(double factor) const;
    Color darken(double factor) const;
    Color lerp(const Color& other, double t) const;
    constexpr Color with_alpha(uint8_t new_a) const noexcept {
        return Color(r, g, b, new_a);
    }
    Color with_alpha_f(double new_a) const;
    double relative_luminance() const;
    Color get_contrast_color(const Color& light_fg = Color(255, 255, 255, 255), const Color& dark_fg = Color(15, 23, 42, 255)) const;
    std::string to_hex(bool include_alpha = false) const;
};

} // namespace tkblend
