#include "color.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>

namespace tkblend {

BLRgba32 Color::to_bl_rgba32() const noexcept {
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

Color Color::with_alpha_f(double new_a) const {
    uint8_t na = static_cast<uint8_t>(std::clamp(new_a * 255.0 + 0.5, 0.0, 255.0));
    return Color(r, g, b, na);
}

double Color::relative_luminance() const {
    auto lin = [](double c) -> double {
        return (c <= 0.04045) ? (c / 12.92) : std::pow((c + 0.055) / 1.055, 2.4);
    };
    double rf = lin(static_cast<double>(r) / 255.0);
    double gf = lin(static_cast<double>(g) / 255.0);
    double bf = lin(static_cast<double>(b) / 255.0);
    return 0.2126 * rf + 0.7152 * gf + 0.0722 * bf;
}

Color Color::get_contrast_color(const Color& light_fg, const Color& dark_fg) const {
    return (relative_luminance() > 0.45) ? dark_fg : light_fg;
}

std::string Color::to_hex(bool include_alpha) const {
    char buf[10];
    if (include_alpha) {
        std::snprintf(buf, sizeof(buf), "#%02x%02x%02x%02x", r, g, b, a);
    } else {
        std::snprintf(buf, sizeof(buf), "#%02x%02x%02x", r, g, b);
    }
    return std::string(buf);
}

} // namespace tkblend
