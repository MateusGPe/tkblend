#include "color.hpp"
#include <algorithm>
#include <cmath>

namespace tkblend {

namespace {

inline int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
}

inline uint8_t parse_2hex(const char* s) {
    return static_cast<uint8_t>((hex_digit(s[0]) << 4) | hex_digit(s[1]));
}

inline uint8_t parse_1hex(char c) {
    return static_cast<uint8_t>(hex_digit(c) * 17);
}

} // anonymous namespace

Color Color::from_hex(const std::string& hex) {
    std::string_view sv = hex;
    if (!sv.empty() && sv.front() == '#') {
        sv.remove_prefix(1);
    }

    switch (sv.size()) {
        case 3: // #RGB
            return Color(parse_1hex(sv[0]), parse_1hex(sv[1]), parse_1hex(sv[2]), 255);
        case 4: // #RGBA
            return Color(parse_1hex(sv[0]), parse_1hex(sv[1]), parse_1hex(sv[2]), parse_1hex(sv[3]));
        case 6: // #RRGGBB
            return Color(parse_2hex(&sv[0]), parse_2hex(&sv[2]), parse_2hex(&sv[4]), 255);
        case 8: // #RRGGBBAA
            return Color(parse_2hex(&sv[0]), parse_2hex(&sv[2]), parse_2hex(&sv[4]), parse_2hex(&sv[6]));
        default:
            return Color(0, 0, 0, 255);
    }
}

Color Color::from_u32(uint32_t argb) {
    uint8_t a = static_cast<uint8_t>((argb >> 24) & 0xFF);
    uint8_t r = static_cast<uint8_t>((argb >> 16) & 0xFF);
    uint8_t g = static_cast<uint8_t>((argb >> 8) & 0xFF);
    uint8_t b = static_cast<uint8_t>(argb & 0xFF);
    return Color(r, g, b, a);
}

uint32_t Color::to_u32() const {
    return (static_cast<uint32_t>(a) << 24) |
           (static_cast<uint32_t>(r) << 16) |
           (static_cast<uint32_t>(g) << 8)  |
            static_cast<uint32_t>(b);
}

BLRgba32 Color::to_bl_rgba32() const {
    return BLRgba32(r, g, b, a);
}

Color Color::lighten(double factor) const {
    if (factor <= 0.0) return Color(0, 0, 0, a);
    double rf = std::min(255.0, static_cast<double>(r) * factor);
    double gf = std::min(255.0, static_cast<double>(g) * factor);
    double bf = std::min(255.0, static_cast<double>(b) * factor);
    return Color(static_cast<uint8_t>(rf + 0.5),
                 static_cast<uint8_t>(gf + 0.5),
                 static_cast<uint8_t>(bf + 0.5),
                 a);
}

Color Color::darken(double factor) const {
    double f = factor;
    if (f > 1.0) f = 1.0 / f;
    f = std::clamp(f, 0.0, 1.0);
    return Color(static_cast<uint8_t>(static_cast<double>(r) * f + 0.5),
                 static_cast<uint8_t>(static_cast<double>(g) * f + 0.5),
                 static_cast<uint8_t>(static_cast<double>(b) * f + 0.5),
                 a);
}

Color Color::lerp(const Color& other, double t) const {
    double clamped_t = std::clamp(t, 0.0, 1.0);
    uint8_t nr = static_cast<uint8_t>(static_cast<double>(r) + (static_cast<double>(other.r) - static_cast<double>(r)) * clamped_t + 0.5);
    uint8_t ng = static_cast<uint8_t>(static_cast<double>(g) + (static_cast<double>(other.g) - static_cast<double>(g)) * clamped_t + 0.5);
    uint8_t nb = static_cast<uint8_t>(static_cast<double>(b) + (static_cast<double>(other.b) - static_cast<double>(b)) * clamped_t + 0.5);
    uint8_t na = static_cast<uint8_t>(static_cast<double>(a) + (static_cast<double>(other.a) - static_cast<double>(a)) * clamped_t + 0.5);
    return Color(nr, ng, nb, na);
}

Color Color::with_alpha(uint8_t new_a) const {
    return Color(r, g, b, new_a);
}

Color Color::with_alpha_f(double new_a) const {
    uint8_t na = static_cast<uint8_t>(std::clamp(new_a * 255.0 + 0.5, 0.0, 255.0));
    return Color(r, g, b, na);
}

} // namespace tkblend
