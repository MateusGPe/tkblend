#include "tkblend.hpp"
#include "font/font_resolver.hpp"

#include <ft2build.h>
#include FT_FREETYPE_H

#include <optional>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/optional.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <iomanip>

namespace nb = nanobind;
namespace fs = std::filesystem;

namespace tkblend {

// -----------------------------------------------------------------------------
// Color Implementation
// -----------------------------------------------------------------------------

Color Color::from_hex(const std::string& hex) {
    std::string s = hex;
    if (!s.empty() && s[0] == '#') {
        s = s.substr(1);
    }
    uint32_t val = 0;
    std::stringstream ss;
    ss << std::hex << s;
    ss >> val;

    if (s.size() == 3) {
        // #RGB
        uint8_t r = ((val >> 8) & 0xF) * 17;
        uint8_t g = ((val >> 4) & 0xF) * 17;
        uint8_t b = (val & 0xF) * 17;
        return Color(r, g, b, 255);
    } else if (s.size() == 4) {
        // #RGBA
        uint8_t r = ((val >> 12) & 0xF) * 17;
        uint8_t g = ((val >> 8) & 0xF) * 17;
        uint8_t b = ((val >> 4) & 0xF) * 17;
        uint8_t a = (val & 0xF) * 17;
        return Color(r, g, b, a);
    } else if (s.size() == 6) {
        // #RRGGBB
        uint8_t r = (val >> 16) & 0xFF;
        uint8_t g = (val >> 8) & 0xFF;
        uint8_t b = val & 0xFF;
        return Color(r, g, b, 255);
    } else if (s.size() == 8) {
        // #RRGGBBAA
        uint8_t r = (val >> 24) & 0xFF;
        uint8_t g = (val >> 16) & 0xFF;
        uint8_t b = (val >> 8) & 0xFF;
        uint8_t a = val & 0xFF;
        return Color(r, g, b, a);
    }
    return Color(0, 0, 0, 255);
}

Color Color::from_u32(uint32_t argb) {
    uint8_t a = (argb >> 24) & 0xFF;
    uint8_t r = (argb >> 16) & 0xFF;
    uint8_t g = (argb >> 8) & 0xFF;
    uint8_t b = argb & 0xFF;
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
    f = std::max(0.0, std::min(1.0, f));
    return Color(static_cast<uint8_t>(static_cast<double>(r) * f + 0.5),
                 static_cast<uint8_t>(static_cast<double>(g) * f + 0.5),
                 static_cast<uint8_t>(static_cast<double>(b) * f + 0.5),
                 a);
}

Color Color::lerp(const Color& other, double t) const {
    double clamped_t = std::max(0.0, std::min(1.0, t));
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
    uint8_t na = static_cast<uint8_t>(std::max(0.0, std::min(255.0, new_a * 255.0 + 0.5)));
    return Color(r, g, b, na);
}

// -----------------------------------------------------------------------------
// Easing & Spring Math
// -----------------------------------------------------------------------------

double ease(int easing_type, double t) {
    double x = std::max(0.0, std::min(1.0, t));
    EasingType et = static_cast<EasingType>(easing_type);
    constexpr double PI = 3.14159265358979323846;
    constexpr double c1 = 1.70158;
    constexpr double c2 = c1 * 1.525;
    constexpr double c3 = c1 + 1.0;
    constexpr double c4 = (2.0 * PI) / 3.0;
    constexpr double c5 = (2.0 * PI) / 4.5;

    auto bounce_out = [](double n) -> double {
        constexpr double n1 = 7.5625;
        constexpr double d1 = 2.75;
        if (n < 1.0 / d1) {
            return n1 * n * n;
        } else if (n < 2.0 / d1) {
            n -= 1.5 / d1;
            return n1 * n * n + 0.75;
        } else if (n < 2.5 / d1) {
            n -= 2.25 / d1;
            return n1 * n * n + 0.9375;
        } else {
            n -= 2.625 / d1;
            return n1 * n * n + 0.984375;
        }
    };

    switch (et) {
        case EasingType::Linear: return x;
        case EasingType::QuadIn: return x * x;
        case EasingType::QuadOut: return 1.0 - (1.0 - x) * (1.0 - x);
        case EasingType::QuadInOut: return x < 0.5 ? 2.0 * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 2.0) / 2.0;
        case EasingType::CubicIn: return x * x * x;
        case EasingType::CubicOut: return 1.0 - std::pow(1.0 - x, 3.0);
        case EasingType::CubicInOut: return x < 0.5 ? 4.0 * x * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 3.0) / 2.0;
        case EasingType::QuartIn: return x * x * x * x;
        case EasingType::QuartOut: return 1.0 - std::pow(1.0 - x, 4.0);
        case EasingType::QuartInOut: return x < 0.5 ? 8.0 * x * x * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 4.0) / 2.0;
        case EasingType::SineIn: return 1.0 - std::cos((x * PI) / 2.0);
        case EasingType::SineOut: return std::sin((x * PI) / 2.0);
        case EasingType::SineInOut: return -(std::cos(PI * x) - 1.0) / 2.0;
        case EasingType::ExpoIn: return x == 0.0 ? 0.0 : std::pow(2.0, 10.0 * x - 10.0);
        case EasingType::ExpoOut: return x == 1.0 ? 1.0 : 1.0 - std::pow(2.0, -10.0 * x);
        case EasingType::ExpoInOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : (x < 0.5 ? std::pow(2.0, 20.0 * x - 10.0) / 2.0 : (2.0 - std::pow(2.0, -20.0 * x + 10.0)) / 2.0));
        case EasingType::CircIn: return 1.0 - std::sqrt(1.0 - std::pow(x, 2.0));
        case EasingType::CircOut: return std::sqrt(1.0 - std::pow(x - 1.0, 2.0));
        case EasingType::CircInOut: return x < 0.5 ? (1.0 - std::sqrt(1.0 - std::pow(2.0 * x, 2.0))) / 2.0 : (std::sqrt(1.0 - std::pow(-2.0 * x + 2.0, 2.0)) + 1.0) / 2.0;
        case EasingType::ElasticIn: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : -std::pow(2.0, 10.0 * x - 10.0) * std::sin((x * 10.0 - 10.75) * c4));
        case EasingType::ElasticOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : std::pow(2.0, -10.0 * x) * std::sin((x * 10.0 - 0.75) * c4) + 1.0);
        case EasingType::ElasticInOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : (x < 0.5 ? -(std::pow(2.0, 20.0 * x - 10.0) * std::sin((20.0 * x - 11.125) * c5)) / 2.0 : (std::pow(2.0, -20.0 * x + 10.0) * std::sin((20.0 * x - 11.125) * c5)) / 2.0 + 1.0));
        case EasingType::BackIn: return c3 * x * x * x - c1 * x * x;
        case EasingType::BackOut: return 1.0 + c3 * std::pow(x - 1.0, 3.0) + c1 * std::pow(x - 1.0, 2.0);
        case EasingType::BackInOut: return x < 0.5 ? (std::pow(2.0 * x, 2.0) * ((c2 + 1.0) * 2.0 * x - c2)) / 2.0 : (std::pow(2.0 * x - 2.0, 2.0) * ((c2 + 1.0) * (x * 2.0 - 2.0) + c2) + 2.0) / 2.0;
        case EasingType::BounceIn: return 1.0 - bounce_out(1.0 - x);
        case EasingType::BounceOut: return bounce_out(x);
        case EasingType::BounceInOut: return x < 0.5 ? (1.0 - bounce_out(1.0 - 2.0 * x)) / 2.0 : (1.0 + bounce_out(2.0 * x - 1.0)) / 2.0;
    }
    return x;
}

double spring(double t, double mass, double stiffness, double damping) {
    if (t <= 0.0) return 0.0;
    if (t >= 1.0) return 1.0;
    double m = std::max(0.001, mass);
    double k = std::max(0.001, stiffness);
    double c = std::max(0.0, damping);
    double w0 = std::sqrt(k / m);
    double zeta = c / (2.0 * std::sqrt(k * m));

    if (zeta < 1.0) {
        double wd = w0 * std::sqrt(1.0 - zeta * zeta);
        return 1.0 - std::exp(-zeta * w0 * t) * (std::cos(wd * t) + (zeta / std::sqrt(1.0 - zeta * zeta)) * std::sin(wd * t));
    } else {
        return 1.0 - (1.0 + w0 * t) * std::exp(-w0 * t);
    }
}

// -----------------------------------------------------------------------------
// DrawBatch Implementation
// -----------------------------------------------------------------------------

void DrawBatch::clear(const Color& c) {
    DrawOp op; op.type = DrawOpType::Clear; op.c1 = c; ops.push_back(std::move(op));
}
void DrawBatch::fill_rect(double x, double y, double w, double h, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::stroke_rect(double x, double y, double w, double h, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.d[6]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::fill_circle(double cx, double cy, double r, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillCircle; op.d[0]=cx; op.d[1]=cy; op.d[2]=r; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::stroke_circle(double cx, double cy, double r, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeCircle; op.d[0]=cx; op.d[1]=cy; op.d[2]=r; op.d[3]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::draw_line(double x1, double y1, double x2, double y2, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::DrawLine; op.d[0]=x1; op.d[1]=y1; op.d[2]=x2; op.d[3]=y2; op.d[4]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}
void DrawBatch::draw_text(const std::string& text, double x, double y, float font_size, const std::string& font_family, const Color& c, int align, int weight, bool italic) {
    DrawOp op; op.type = DrawOpType::DrawText; op.str = text; op.d[0]=x; op.d[1]=y; op.d[2]=font_size; op.c1=c; op.i1=align; op.i2=weight; op.i3=italic ? 1 : 0;
    ops.push_back(std::move(op));
}
void DrawBatch::draw_shadow_rounded_rect(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const Color& shadow_color) {
    DrawOp op; op.type = DrawOpType::DrawShadowRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.d[6]=blur_radius; op.d[7]=spread; op.c1=shadow_color; ops.push_back(std::move(op));
}
void DrawBatch::draw_card(double x, double y, double w, double h, double rx, double ry, const Color& bg, const Color& border, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const Color& shadow_col) {
    DrawOp op; op.type = DrawOpType::DrawCard; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.d[6]=border_w; op.d[7]=shadow_blur; op.c1=bg; op.c2=border; ops.push_back(std::move(op));
}
void DrawBatch::save() { DrawOp op; op.type = DrawOpType::Save; ops.push_back(std::move(op)); }
void DrawBatch::restore() { DrawOp op; op.type = DrawOpType::Restore; ops.push_back(std::move(op)); }
void DrawBatch::translate(double tx, double ty) { DrawOp op; op.type = DrawOpType::Translate; op.d[0]=tx; op.d[1]=ty; ops.push_back(std::move(op)); }
void DrawBatch::scale(double sx, double sy) { DrawOp op; op.type = DrawOpType::Scale; op.d[0]=sx; op.d[1]=sy; ops.push_back(std::move(op)); }
void DrawBatch::rotate(double rad) { DrawOp op; op.type = DrawOpType::Rotate; op.d[0]=rad; ops.push_back(std::move(op)); }
void DrawBatch::clip_rect(double x, double y, double w, double h) { DrawOp op; op.type = DrawOpType::ClipRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; ops.push_back(std::move(op)); }
void DrawBatch::clip_rounded_rect(double x, double y, double w, double h, double rx, double ry) { DrawOp op; op.type = DrawOpType::ClipRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; ops.push_back(std::move(op)); }
void DrawBatch::reset_clip() { DrawOp op; op.type = DrawOpType::ResetClip; ops.push_back(std::move(op)); }
void DrawBatch::reset() { ops.clear(); }

// -----------------------------------------------------------------------------
// Gradient Implementation
// -----------------------------------------------------------------------------

Gradient Gradient::create_linear(double x0, double y0, double x1, double y1) {
    Gradient g;
    g.type = Type::Linear;
    g.x0 = x0; g.y0 = y0;
    g.x1 = x1; g.y1 = y1;
    return g;
}

Gradient Gradient::create_radial(double x0, double y0, double r0, double x1, double y1, double r1) {
    Gradient g;
    g.type = Type::Radial;
    g.x0 = x0; g.y0 = y0; g.r0 = r0;
    g.x1 = x1; g.y1 = y1; g.r1 = r1;
    return g;
}

void Gradient::add_stop(double offset, const Color& color) {
    stops.emplace_back(std::clamp(offset, 0.0, 1.0), color);
}

void Gradient::set_extend_mode(int mode) {
    extend_mode = static_cast<BLExtendMode>(mode);
}

BLGradient Gradient::to_bl_gradient() const {
    BLGradient bl_g;
    if (type == Type::Linear) {
        bl_g = BLGradient(BLLinearGradientValues(x0, y0, x1, y1));
    } else {
        bl_g = BLGradient(BLRadialGradientValues(x0, y0, r0, x1, y1, r1));
    }
    bl_g.set_extend_mode(extend_mode);
    for (const auto& stop : stops) {
        bl_g.add_stop(stop.first, stop.second.to_bl_rgba32());
    }
    return bl_g;
}

// -----------------------------------------------------------------------------
// Path Implementation
// -----------------------------------------------------------------------------

Path& Path::move_to(double x, double y) { path.move_to(x, y); return *this; }
Path& Path::line_to(double x, double y) { path.line_to(x, y); return *this; }
Path& Path::quad_to(double x1, double y1, double x2, double y2) { path.quad_to(x1, y1, x2, y2); return *this; }
Path& Path::cubic_to(double x1, double y1, double x2, double y2, double x3, double y3) {
    path.cubic_to(x1, y1, x2, y2, x3, y3);
    return *this;
}
Path& Path::arc_to(double cx, double cy, double rx, double ry, double start_angle, double sweep_angle) {
    path.arc_to(cx, cy, rx, ry, start_angle, sweep_angle);
    return *this;
}
Path& Path::add_rect(double x, double y, double w, double h) {
    path.add_rect(BLRect(x, y, w, h));
    return *this;
}
Path& Path::add_rounded_rect(double x, double y, double w, double h, double rx, double ry) {
    path.add_round_rect(BLRoundRect(x, y, w, h, rx, ry));
    return *this;
}
Path& Path::add_circle(double cx, double cy, double r) {
    path.add_circle(BLCircle(cx, cy, r));
    return *this;
}
Path& Path::add_ellipse(double cx, double cy, double rx, double ry) {
    path.add_ellipse(BLEllipse(cx, cy, rx, ry));
    return *this;
}
Path& Path::close() { path.close(); return *this; }
Path& Path::clear() { path.clear(); return *this; }
Path& Path::reset() { path.reset(); return *this; }

// -----------------------------------------------------------------------------
// FontManager Implementation
// -----------------------------------------------------------------------------

FontManager& FontManager::instance() {
    static FontManager instance;
    return instance;
}

FontManager::FontManager() {
    // Fully lazy on-demand initialization. Zero blocking I/O at startup.
}

std::string FontManager::resolve_system_font_path(const std::string& family, int weight, bool italic) {
    std::string lower_family = family;
    std::transform(lower_family.begin(), lower_family.end(), lower_family.begin(), ::tolower);

    if (lower_family.empty() || lower_family == "default") {
        lower_family = default_font_family_.empty() ? "sans-serif" : default_font_family_;
    }

    std::string cache_key = lower_family;
    if (weight != 400 || italic) {
        cache_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
    }

    // 1. Check cached paths
    auto it = font_paths_.find(cache_key);
    if (it != font_paths_.end()) {
        try {
            if (fs::exists(it->second)) {
                return it->second;
            }
        } catch (...) {}
    }

    // 2. Query native platform resolver (DirectWrite/GDI on Win, CoreText on macOS, Fontconfig on Linux)
    std::string native_path = resolve_native_font_path(family, weight, italic);
    if (native_path.empty() && lower_family != family) {
        native_path = resolve_native_font_path(lower_family, weight, italic);
    }

    if (!native_path.empty()) {
        try {
            if (fs::exists(native_path)) {
                font_paths_[cache_key] = native_path;
                return native_path;
            }
        } catch (...) {}
    }

    return "";
}

bool FontManager::load_font_face(const std::string& name, const std::string& filepath) {
    try {
        if (!fs::exists(filepath)) {
            return false;
        }
    } catch (...) {
        return false;
    }

    std::lock_guard<std::mutex> lock(mutex_);
    BLFontFace face;
    BLResult result = face.create_from_file(filepath.c_str());
    if (result == BL_SUCCESS) {
        std::string lower_name = name;
        std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
        font_faces_[lower_name] = face;
        font_paths_[lower_name] = filepath;

        // Register canonical family name from OpenType metadata
        const BLString& fam = face.family_name();
        if (!fam.is_empty()) {
            std::string real_fam = fam.data();
            std::string lower_real = real_fam;
            std::transform(lower_real.begin(), lower_real.end(), lower_real.begin(), ::tolower);
            if (lower_real != lower_name) {
                font_faces_[lower_real] = face;
                font_paths_[lower_real] = filepath;
            }
        }

        if (default_font_family_.empty() || lower_name == "sans-serif" || lower_name == "default") {
            default_font_family_ = lower_name;
        }
        return true;
    }
    return false;
}

std::string FontManager::find_system_font(const std::string& family, int weight, bool italic) {
    std::lock_guard<std::mutex> lock(mutex_);
    return resolve_system_font_path(family, weight, italic);
}

std::vector<std::string> FontManager::get_loaded_fonts() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> fonts;
    fonts.reserve(font_faces_.size());
    for (const auto& kv : font_faces_) {
        fonts.push_back(kv.first);
    }
    std::sort(fonts.begin(), fonts.end());
    return fonts;
}

std::vector<std::string> FontManager::get_system_fonts(bool refresh) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!system_fonts_cache_.empty() && !refresh) {
        return system_fonts_cache_;
    }
    system_fonts_cache_ = get_native_system_fonts();
    std::sort(system_fonts_cache_.begin(), system_fonts_cache_.end());
    return system_fonts_cache_;
}

int FontManager::register_font_directory(const std::string& dir_path) {
    int count = 0;
    try {
        if (!fs::exists(dir_path)) return 0;
        for (const auto& entry : fs::recursive_directory_iterator(dir_path, fs::directory_options::skip_permission_denied)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                if (ext == ".ttf" || ext == ".otf" || ext == ".ttc") {
                    std::string stem = entry.path().stem().string();
                    std::string p = entry.path().string();
                    if (load_font_face(stem, p)) {
                        count++;
                    }
                }
            }
        }
    } catch (...) {
        // Ignore directory scanning exceptions
    }
    return count;
}

std::string FontManager::get_active_font() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (default_font_family_.empty()) {
        return "sans-serif";
    }
    return default_font_family_;
}

bool FontManager::set_active_font(const std::string& family_or_path) {
    if (family_or_path.empty()) return false;
    std::string lower = family_or_path;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    try {
        if (fs::exists(family_or_path) && fs::is_regular_file(family_or_path)) {
            std::string stem = fs::path(family_or_path).stem().string();
            if (load_font_face(stem, family_or_path)) {
                std::lock_guard<std::mutex> lock(mutex_);
                default_font_family_ = stem;
                return true;
            }
        }
    } catch (...) {}

    // Check if already loaded
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (font_faces_.find(lower) != font_faces_.end()) {
            default_font_family_ = lower;
            return true;
        }
    }

    // Check if resolvable on system
    std::string resolved = resolve_system_font_path(lower, 400, false);
    if (!resolved.empty()) {
        std::lock_guard<std::mutex> lock(mutex_);
        default_font_family_ = lower;
        return true;
    }
    return false;
}

BLFontFace* FontManager::get_font_face(const std::string& family, int weight, bool italic) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string lower_family = family;
    std::transform(lower_family.begin(), lower_family.end(), lower_family.begin(), ::tolower);

    if (lower_family.empty() || lower_family == "default") {
        lower_family = default_font_family_.empty() ? "sans-serif" : default_font_family_;
    }

    std::string cache_key = lower_family;
    if (weight != 400 || italic) {
        cache_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
    }

    // 1. Check already loaded face
    auto it = font_faces_.find(cache_key);
    if (it != font_faces_.end()) {
        return &it->second;
    }

    // 2. Lazily resolve path
    std::string path = resolve_system_font_path(lower_family, weight, italic);
    if (!path.empty()) {
        BLFontFace face;
        if (face.create_from_file(path.c_str()) == BL_SUCCESS) {
            auto inserted = font_faces_.emplace(cache_key, face);
            font_paths_[cache_key] = path;

            const BLString& fam = face.family_name();
            if (!fam.is_empty()) {
                std::string real_fam = fam.data();
                std::string lower_real = real_fam;
                std::transform(lower_real.begin(), lower_real.end(), lower_real.begin(), ::tolower);
                if (lower_real != lower_family) {
                    std::string real_key = lower_real;
                    if (weight != 400 || italic) {
                        real_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
                    }
                    font_faces_.emplace(real_key, face);
                    font_paths_[real_key] = path;
                }
            }

            if (default_font_family_.empty()) {
                default_font_family_ = lower_family;
            }
            return &inserted.first->second;
        }
    }

    // 3. Fallback to base family without weight/italic if not found
    if (cache_key != lower_family) {
        auto base_it = font_faces_.find(lower_family);
        if (base_it != font_faces_.end()) {
            return &base_it->second;
        }
    }

    // 4. Fallback to sans-serif
    if (lower_family != "sans-serif") {
        auto sans_it = font_faces_.find("sans-serif");
        if (sans_it != font_faces_.end()) {
            return &sans_it->second;
        }

        std::string default_path = resolve_system_font_path("sans-serif", weight, italic);
        if (default_path.empty()) {
            default_path = resolve_system_font_path("sans-serif", 400, false);
        }
        if (!default_path.empty()) {
            BLFontFace face;
            if (face.create_from_file(default_path.c_str()) == BL_SUCCESS) {
                auto inserted = font_faces_.emplace("sans-serif", face);
                font_paths_["sans-serif"] = default_path;
                if (default_font_family_.empty()) {
                    default_font_family_ = "sans-serif";
                }
                return &inserted.first->second;
            }
        }
    }

    // 5. Any available font face
    if (!font_faces_.empty()) {
        return &font_faces_.begin()->second;
    }

    return nullptr;
}

BLFont FontManager::create_font(const std::string& family, float size, int weight, bool italic) {
    BLFontFace* face = get_font_face(family, weight, italic);
    BLFont font;
    if (face && face->is_valid()) {
        font.create_from_face(*face, size);
    }
    return font;
}

// -----------------------------------------------------------------------------
// ShadowEngine Implementation (Fast 3-pass Box Blur & Caching)
// -----------------------------------------------------------------------------

ShadowEngine& ShadowEngine::instance() {
    static ShadowEngine instance;
    return instance;
}

void ShadowEngine::apply_3pass_box_blur(BLImageData& data, double blur_radius) {
    if (blur_radius <= 0.0) return;

    int w = static_cast<int>(data.size.w);
    int h = static_cast<int>(data.size.h);
    if (w <= 0 || h <= 0) return;

    int stride = static_cast<int>(data.stride);
    uint8_t* pixels = static_cast<uint8_t*>(data.pixel_data);

    // Compute standard 3-box approximation of Gaussian sigma
    double sigma = blur_radius / 2.0;
    double wIdeal = std::sqrt((12.0 * sigma * sigma / 3.0) + 1.0);
    int wl = static_cast<int>(std::floor(wIdeal));
    if (wl % 2 == 0) wl--;
    int wu = wl + 2;
    double mIdeal = (12.0 * sigma * sigma - 3.0 * wl * wl - 12.0 * wl - 9.0) / (-4.0 * wl - 4.0);
    int m = static_cast<int>(std::round(mIdeal));

    int box_r[3];
    for (int i = 0; i < 3; ++i) {
        int box_w = (i < m ? wl : wu);
        box_r[i] = std::max(1, (box_w - 1) / 2);
    }

    std::vector<uint8_t> temp(w * h * 4);

    // Perform 3 horizontal + vertical passes on 32-bit PRGB buffer
    for (int pass = 0; pass < 3; ++pass) {
        int r = box_r[pass];
        float inv_w = 1.0f / (2.0f * r + 1.0f);

        // Horizontal Pass: pixels -> temp
        for (int y = 0; y < h; ++y) {
            uint8_t* src_row = pixels + y * stride;
            uint8_t* dst_row = temp.data() + (y * w) * 4;

            int sum_b = src_row[0] * (r + 1);
            int sum_g = src_row[1] * (r + 1);
            int sum_r = src_row[2] * (r + 1);
            int sum_a = src_row[3] * (r + 1);

            for (int i = 0; i < r; ++i) {
                int cx = std::min(i, w - 1) * 4;
                sum_b += src_row[cx + 0];
                sum_g += src_row[cx + 1];
                sum_r += src_row[cx + 2];
                sum_a += src_row[cx + 3];
            }

            for (int x = 0; x < w; ++x) {
                int right_x = std::min(x + r, w - 1) * 4;
                int left_x = std::max(x - r - 1, 0) * 4;

                dst_row[x * 4 + 0] = static_cast<uint8_t>(sum_b * inv_w);
                dst_row[x * 4 + 1] = static_cast<uint8_t>(sum_g * inv_w);
                dst_row[x * 4 + 2] = static_cast<uint8_t>(sum_r * inv_w);
                dst_row[x * 4 + 3] = static_cast<uint8_t>(sum_a * inv_w);

                sum_b += src_row[right_x + 0] - src_row[left_x + 0];
                sum_g += src_row[right_x + 1] - src_row[left_x + 1];
                sum_r += src_row[right_x + 2] - src_row[left_x + 2];
                sum_a += src_row[right_x + 3] - src_row[left_x + 3];
            }
        }

        // Vertical Pass: temp -> pixels
        float inv_h = inv_w;
        for (int x = 0; x < w; ++x) {
            int sum_b = temp[(0 * w + x) * 4 + 0] * (r + 1);
            int sum_g = temp[(0 * w + x) * 4 + 1] * (r + 1);
            int sum_r = temp[(0 * w + x) * 4 + 2] * (r + 1);
            int sum_a = temp[(0 * w + x) * 4 + 3] * (r + 1);

            for (int i = 0; i < r; ++i) {
                int cy = std::min(i, h - 1);
                sum_b += temp[(cy * w + x) * 4 + 0];
                sum_g += temp[(cy * w + x) * 4 + 1];
                sum_r += temp[(cy * w + x) * 4 + 2];
                sum_a += temp[(cy * w + x) * 4 + 3];
            }

            for (int y = 0; y < h; ++y) {
                uint8_t* dst_ptr = pixels + y * stride + x * 4;
                int right_y = std::min(y + r, h - 1);
                int left_y = std::max(y - r - 1, 0);

                dst_ptr[0] = static_cast<uint8_t>(sum_b * inv_h);
                dst_ptr[1] = static_cast<uint8_t>(sum_g * inv_h);
                dst_ptr[2] = static_cast<uint8_t>(sum_r * inv_h);
                dst_ptr[3] = static_cast<uint8_t>(sum_a * inv_h);

                sum_b += temp[(right_y * w + x) * 4 + 0] - temp[(left_y * w + x) * 4 + 0];
                sum_g += temp[(right_y * w + x) * 4 + 1] - temp[(left_y * w + x) * 4 + 1];
                sum_r += temp[(right_y * w + x) * 4 + 2] - temp[(left_y * w + x) * 4 + 2];
                sum_a += temp[(right_y * w + x) * 4 + 3] - temp[(left_y * w + x) * 4 + 3];
            }
        }
    }
}

BLImage ShadowEngine::get_or_render_rounded_shadow(
    double w, double h, double rx, double ry,
    double blur_radius, double spread,
    const Color& shadow_color,
    int& out_pad_x, int& out_pad_y
) {
    int iw = static_cast<int>(std::round(w));
    int ih = static_cast<int>(std::round(h));
    int irx = static_cast<int>(std::round(rx));
    int iry = static_cast<int>(std::round(ry));
    int iblur = static_cast<int>(std::round(blur_radius * 10.0));
    int ispread = static_cast<int>(std::round(spread * 10.0));
    uint32_t col_u32 = shadow_color.to_u32();

    ShadowKey key{iw, ih, irx, iry, iblur, ispread, col_u32};

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = cache_map_.find(key);
    if (it != cache_map_.end()) {
        lru_list_.splice(lru_list_.begin(), lru_list_, it->second);
        out_pad_x = it->second->pad_x;
        out_pad_y = it->second->pad_y;
        return it->second->image;
    }

    // Render new shadow
    int pad = static_cast<int>(std::ceil(blur_radius * 2.5 + std::abs(spread) + 4.0));
    out_pad_x = pad;
    out_pad_y = pad;

    int mask_w = iw + static_cast<int>(std::round(spread * 2.0)) + pad * 2;
    int mask_h = ih + static_cast<int>(std::round(spread * 2.0)) + pad * 2;

    if (mask_w <= 0 || mask_h <= 0) {
        return BLImage();
    }

    BLImage shadow_img(mask_w, mask_h, BL_FORMAT_PRGB32);
    BLContext sctx(shadow_img);
    sctx.clear_all();

    double geom_x = pad - spread;
    double geom_y = pad - spread;
    double geom_w = w + spread * 2.0;
    double geom_h = h + spread * 2.0;
    double geom_rx = std::max(0.0, rx + spread);
    double geom_ry = std::max(0.0, ry + spread);

    sctx.set_fill_style(shadow_color.to_bl_rgba32());
    sctx.fill_round_rect(BLRoundRect(geom_x, geom_y, geom_w, geom_h, geom_rx, geom_ry));
    sctx.end();

    if (blur_radius > 0.1) {
        BLImageData img_data;
        shadow_img.make_mutable(&img_data);
        apply_3pass_box_blur(img_data, blur_radius);
    }

    // Store in LRU cache
    if (lru_list_.size() >= max_cache_entries_) {
        auto last = lru_list_.end();
        --last;
        cache_map_.erase(last->key);
        lru_list_.pop_back();
    }

    lru_list_.push_front(CachedShadow{key, shadow_img, pad, pad});
    cache_map_[key] = lru_list_.begin();

    return shadow_img;
}

// -----------------------------------------------------------------------------
// EmojiEngine Implementation
// -----------------------------------------------------------------------------

EmojiEngine& EmojiEngine::instance() {
    static EmojiEngine instance;
    return instance;
}

EmojiEngine::EmojiEngine() {
    emoji_font_path_ = resolve_system_emoji_font();
}

EmojiEngine::~EmojiEngine() {
    if (ft_face_) {
        FT_Done_Face(reinterpret_cast<FT_Face>(ft_face_));
        ft_face_ = nullptr;
    }
    if (ft_lib_) {
        FT_Done_FreeType(reinterpret_cast<FT_Library>(ft_lib_));
        ft_lib_ = nullptr;
    }
}

std::string EmojiEngine::resolve_system_emoji_font() {
#ifdef __linux__
    static const char* linux_paths[] = {
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf",
        "/usr/share/fonts/google-noto-color-emoji-fonts/NotoColorEmoji.ttf",
        "/home/mateusgp/.local/share/fonts/NotoColorEmoji.ttf"
    };
    for (const char* p : linux_paths) {
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
    }
#if defined(__linux__)
    std::string fc_emoji = resolve_native_font_path("emoji");
    if (!fc_emoji.empty()) {
        try {
            if (fs::exists(fc_emoji)) return fc_emoji;
        } catch (...) {}
    }
#endif
#elif defined(_WIN32)
    std::string win_dir = "C:\\Windows";
    if (const char* w = std::getenv("WINDIR")) win_dir = w;
    else if (const char* sr = std::getenv("SystemRoot")) win_dir = sr;
    std::string seg = win_dir + "\\Fonts\\seguiemj.ttf";
    try {
        if (fs::exists(seg)) return seg;
    } catch (...) {}
#elif defined(__APPLE__)
    static const char* mac_paths[] = {
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Core/Apple Color Emoji.ttc",
        "/Library/Fonts/Apple Color Emoji.ttc"
    };
    for (const char* p : mac_paths) {
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
    }
#endif
    return "";
}

bool EmojiEngine::init() {
    if (initialized_) return (ft_face_ != nullptr);
    initialized_ = true;

    FT_Library ft = nullptr;
    if (FT_Init_FreeType(&ft) != 0) {
        return false;
    }
    ft_lib_ = ft;

    if (emoji_font_path_.empty()) {
        emoji_font_path_ = resolve_system_emoji_font();
    }
    if (emoji_font_path_.empty()) {
        return false;
    }
    try {
        if (!fs::exists(emoji_font_path_)) return false;
    } catch (...) {
        return false;
    }

    FT_Face face = nullptr;
    if (FT_New_Face(ft, emoji_font_path_.c_str(), 0, &face) != 0) {
        return false;
    }
    ft_face_ = face;

    if (face->num_fixed_sizes > 0) {
        FT_Select_Size(face, 0);
    }
    return true;
}

void EmojiEngine::set_emoji_font(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (path == emoji_font_path_) return;
    emoji_font_path_ = path;
    cache_.clear();

    if (ft_face_) {
        FT_Done_Face(reinterpret_cast<FT_Face>(ft_face_));
        ft_face_ = nullptr;
    }
    if (ft_lib_) {
        FT_Done_FreeType(reinterpret_cast<FT_Library>(ft_lib_));
        ft_lib_ = nullptr;
    }
    initialized_ = false;
    init();
}

std::string EmojiEngine::get_emoji_font_path() {
    std::lock_guard<std::mutex> lock(mutex_);
    return emoji_font_path_;
}

bool EmojiEngine::is_emoji(uint32_t cp) {
    if (cp >= 0x1F300 && cp <= 0x1FAFF) return true;
    if (cp >= 0x2600 && cp <= 0x27BF) return true;
    if (cp >= 0x2B00 && cp <= 0x2BFF) return true;
    if (cp >= 0x2300 && cp <= 0x23FF) return true;
    if (cp >= 0x1F1E6 && cp <= 0x1F1FF) return true;
    if (cp == 0xFE0E || cp == 0xFE0F || cp == 0x200D) return true;
    return false;
}

bool EmojiEngine::get_emoji_glyph(
    uint32_t codepoint,
    float target_size,
    BLImage& out_img,
    double& out_advance_x,
    double& out_bearing_y
) {
    int target_sz_int = static_cast<int>(target_size + 0.5f);
    if (target_sz_int < 1) target_sz_int = 1;

    GlyphKey key{codepoint, target_sz_int};

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = cache_.find(key);
    if (it != cache_.end()) {
        if (!it->second.valid) return false;
        out_img = it->second.image;
        out_advance_x = it->second.advance_x;
        out_bearing_y = it->second.bearing_y;
        return true;
    }

    if (!init()) {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    FT_Face face = reinterpret_cast<FT_Face>(ft_face_);
    if (!face) {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    FT_UInt glyph_index = FT_Get_Char_Index(face, codepoint);
    if (glyph_index == 0) {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    if (FT_Load_Glyph(face, glyph_index, FT_LOAD_COLOR) != 0) {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    FT_GlyphSlot slot = face->glyph;
    if (slot->format != FT_GLYPH_FORMAT_BITMAP) {
        if (FT_Render_Glyph(slot, FT_RENDER_MODE_NORMAL) != 0) {
            cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
            return false;
        }
    }

    FT_Bitmap& bmp = slot->bitmap;
    if (bmp.width == 0 || bmp.rows == 0 || !bmp.buffer) {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    int raw_w = bmp.width;
    int raw_h = bmp.rows;

    BLImage raw_bl_img;
    if (bmp.pixel_mode == FT_PIXEL_MODE_BGRA) {
        raw_bl_img.create_from_data(raw_w, raw_h, BL_FORMAT_PRGB32, bmp.buffer, bmp.pitch);
    } else if (bmp.pixel_mode == FT_PIXEL_MODE_GRAY) {
        raw_bl_img.create(raw_w, raw_h, BL_FORMAT_PRGB32);
        BLImageData img_data;
        if (raw_bl_img.make_mutable(&img_data) == BL_SUCCESS) {
            for (int r = 0; r < raw_h; ++r) {
                const uint8_t* src_row = bmp.buffer + r * bmp.pitch;
                uint32_t* dst_row = reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(img_data.pixel_data) + r * img_data.stride);
                for (int c = 0; c < raw_w; ++c) {
                    uint32_t a = src_row[c];
                    dst_row[c] = (a << 24) | (a << 16) | (a << 8) | a;
                }
            }
        }
    } else {
        cache_[key] = CachedGlyph{BLImage(), 0, 0, false};
        return false;
    }

    double aspect = static_cast<double>(raw_w) / static_cast<double>(raw_h);
    int dest_h = target_sz_int;
    int dest_w = static_cast<int>(dest_h * aspect + 0.5);
    if (dest_w < 1) dest_w = 1;

    BLImage scaled_img;
    scaled_img.create(dest_w, dest_h, BL_FORMAT_PRGB32);
    {
        BLContext sctx(scaled_img);
        sctx.clear_all();
        double sx = static_cast<double>(dest_w) / static_cast<double>(raw_w);
        double sy = static_cast<double>(dest_h) / static_cast<double>(raw_h);
        sctx.scale(sx, sy);
        sctx.blit_image(BLPoint(0, 0), raw_bl_img);
        sctx.end();
    }

    double adv_x = dest_w * 1.15;
    double bear_y = dest_h * 0.82;

    CachedGlyph entry{scaled_img, adv_x, bear_y, true};
    cache_[key] = entry;

    out_img = scaled_img;
    out_advance_x = adv_x;
    out_bearing_y = bear_y;
    return true;
}

// -----------------------------------------------------------------------------
// Surface Implementation
// -----------------------------------------------------------------------------

Surface::Surface(int width, int height)
    : width_(std::max(1, width)), height_(std::max(1, height)) {
    init_context();
}

Surface::~Surface() {
    ctx_.end();
}

void Surface::init_context() {
    ctx_.end();
    image_.create(width_, height_, BL_FORMAT_PRGB32);
    ctx_.begin(image_);
    ctx_.set_comp_op(BL_COMP_OP_SRC_OVER);
}

void Surface::resize(int width, int height) {
    int w = std::max(1, width);
    int h = std::max(1, height);
    if (w == width_ && h == height_) return;

    std::lock_guard<std::mutex> lock(mutex_);
    width_ = w;
    height_ = h;
    init_context();
}

void Surface::clear(const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (color.a == 0) {
        ctx_.clear_all();
    } else {
        ctx_.set_fill_style(color.to_bl_rgba32());
        ctx_.fill_all();
    }
}

void Surface::clear_rect(double x, double y, double w, double h) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.clear_rect(BLRect(x, y, w, h));
}

void Surface::save() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.save();
}

void Surface::restore() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.restore();
}

void Surface::reset_transform() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.user_to_meta();
}

void Surface::translate(double tx, double ty) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.translate(tx, ty);
}

void Surface::scale(double sx, double sy) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.scale(sx, sy);
}

void Surface::rotate(double angle_rad) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.rotate(angle_rad);
}

void Surface::clip_rect(double x, double y, double w, double h) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.clip_to_rect(BLRect(x, y, w, h));
}

void Surface::clip_rounded_rect(double x, double y, double w, double h, double rx, double ry) {
    std::lock_guard<std::mutex> lock(mutex_);
    (void)rx; (void)ry;
    ctx_.clip_to_rect(BLRect(x, y, w, h));
}

void Surface::reset_clip() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.restore_clipping();
}

void Surface::set_comp_op(int comp_op) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_comp_op(static_cast<BLCompOp>(comp_op));
}

void Surface::set_global_alpha(double alpha) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_global_alpha(std::clamp(alpha, 0.0, 1.0));
}

void Surface::fill_rect(double x, double y, double w, double h, const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_rect(BLRect(x, y, w, h));
}

void Surface::fill_rect_gradient(double x, double y, double w, double h, const Gradient& gradient) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(gradient.to_bl_gradient());
    ctx_.fill_rect(BLRect(x, y, w, h));
}

void Surface::stroke_rect(double x, double y, double w, double h, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_rect(BLRect(x, y, w, h));
}

void Surface::fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_round_rect(BLRoundRect(x, y, w, h, rx, ry));
}

void Surface::fill_rounded_rect_gradient(double x, double y, double w, double h, double rx, double ry, const Gradient& gradient) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(gradient.to_bl_gradient());
    ctx_.fill_round_rect(BLRoundRect(x, y, w, h, rx, ry));
}

void Surface::stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_round_rect(BLRoundRect(x, y, w, h, rx, ry));
}

void Surface::fill_circle(double cx, double cy, double r, const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_circle(BLCircle(cx, cy, r));
}

void Surface::fill_circle_gradient(double cx, double cy, double r, const Gradient& gradient) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(gradient.to_bl_gradient());
    ctx_.fill_circle(BLCircle(cx, cy, r));
}

void Surface::stroke_circle(double cx, double cy, double r, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_circle(BLCircle(cx, cy, r));
}

void Surface::fill_ellipse(double cx, double cy, double rx, double ry, const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_ellipse(BLEllipse(cx, cy, rx, ry));
}

void Surface::stroke_ellipse(double cx, double cy, double rx, double ry, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_ellipse(BLEllipse(cx, cy, rx, ry));
}

void Surface::draw_line(double x1, double y1, double x2, double y2, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_line(BLLine(x1, y1, x2, y2));
}

void Surface::fill_path(const Path& path, const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_path(path.path);
}

void Surface::fill_path_gradient(const Path& path, const Gradient& gradient) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_fill_style(gradient.to_bl_gradient());
    ctx_.fill_path(path.path);
}

void Surface::stroke_path(const Path& path, const Color& color, double stroke_width) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.set_stroke_style(color.to_bl_rgba32());
    ctx_.set_stroke_width(stroke_width);
    ctx_.stroke_path(path.path);
}

namespace {
inline uint32_t decode_utf8(const char*& p, const char* end) {
    if (p >= end) return 0;
    unsigned char c = static_cast<unsigned char>(*p++);
    if (c < 0x80) return c;
    if ((c & 0xE0) == 0xC0) {
        if (p >= end) return 0;
        return ((c & 0x1F) << 6) | (static_cast<unsigned char>(*p++) & 0x3F);
    }
    if ((c & 0xF0) == 0xE0) {
        if (p + 1 >= end) return 0;
        uint32_t cp = ((c & 0x0F) << 12);
        cp |= (static_cast<unsigned char>(*p++) & 0x3F) << 6;
        cp |= (static_cast<unsigned char>(*p++) & 0x3F);
        return cp;
    }
    if ((c & 0xF8) == 0xF0) {
        if (p + 2 >= end) return 0;
        uint32_t cp = ((c & 0x07) << 18);
        cp |= (static_cast<unsigned char>(*p++) & 0x3F) << 12;
        cp |= (static_cast<unsigned char>(*p++) & 0x3F) << 6;
        cp |= (static_cast<unsigned char>(*p++) & 0x3F);
        return cp;
    }
    return 0;
}
} // anonymous namespace

void Surface::draw_text(
    const std::string& text,
    double x, double y,
    float font_size,
    const std::string& font_family,
    const Color& color,
    int align,
    int weight,
    bool italic
) {
    if (text.empty()) return;
    std::lock_guard<std::mutex> lock(mutex_);
    BLFont font = FontManager::instance().create_font(font_family, font_size, weight, italic);
    if (font.is_empty()) return;

    // Fast check: does text contain any multibyte characters that could be emoji?
    bool has_potential_emoji = false;
    for (size_t i = 0; i < text.size(); ++i) {
        if (static_cast<unsigned char>(text[i]) >= 0x80) {
            const char* p = text.data() + i;
            const char* end = text.data() + text.size();
            uint32_t cp = decode_utf8(p, end);
            if (EmojiEngine::is_emoji(cp)) {
                has_potential_emoji = true;
                break;
            }
            i = (p - text.data()) - 1;
        }
    }

    if (!has_potential_emoji) {
        double draw_x = x;
        double draw_y = y;

        if (align != 0) {
            BLTextMetrics tm;
            BLGlyphBuffer gb;
            gb.set_utf8_text(text.data(), text.size());
            font.get_text_metrics(gb, tm);
            double text_w = tm.advance.x;
            if (text_w <= 0.0) text_w = tm.bounding_box.x1 - tm.bounding_box.x0;
            if (align == 1) {
                draw_x -= text_w / 2.0;
            } else if (align == 2) {
                draw_x -= text_w;
            }
        }

        ctx_.set_fill_style(color.to_bl_rgba32());
        ctx_.fill_utf8_text(BLPoint(draw_x, draw_y), font, text.data(), text.size());
        return;
    }

    // Rich text path with emoji run-splitting
    struct TextRun {
        bool is_emoji;
        std::string text;
        BLImage emoji_img;
        double width;
        double bearing_y;
    };

    std::vector<TextRun> runs;
    std::string cur_text;

    auto flush_text = [&]() {
        if (!cur_text.empty()) {
            BLTextMetrics tm;
            BLGlyphBuffer gb;
            gb.set_utf8_text(cur_text.data(), cur_text.size());
            font.get_text_metrics(gb, tm);
            double w = tm.advance.x;
            if (w <= 0.0) {
                w = tm.bounding_box.x1 - tm.bounding_box.x0;
            }
            if (w <= 0.0) {
                w = cur_text.size() * (font_size * 0.3);
            }
            runs.push_back(TextRun{false, cur_text, BLImage(), w, 0.0});
            cur_text.clear();
        }
    };

    const char* p = text.data();
    const char* end = p + text.size();

    while (p < end) {
        const char* prev_p = p;
        uint32_t cp = decode_utf8(p, end);
        if (cp == 0) break;

        // Skip variation selectors
        if (cp == 0xFE0E || cp == 0xFE0F) {
            continue;
        }

        if (EmojiEngine::is_emoji(cp)) {
            BLImage emoji_img;
            double adv_x = 0, bear_y = 0;
            if (EmojiEngine::instance().get_emoji_glyph(cp, font_size, emoji_img, adv_x, bear_y)) {
                flush_text();
                runs.push_back(TextRun{true, "", emoji_img, adv_x, bear_y});
                continue;
            }
        }

        cur_text.append(prev_p, p - prev_p);
    }
    flush_text();

    if (runs.empty()) return;

    double total_w = 0.0;
    for (const auto& r : runs) {
        total_w += r.width;
    }

    double draw_x = x;
    if (align == 1) {
        draw_x -= total_w / 2.0;
    } else if (align == 2) {
        draw_x -= total_w;
    }

    double curr_x = draw_x;
    ctx_.set_fill_style(color.to_bl_rgba32());

    for (const auto& r : runs) {
        if (r.is_emoji) {
            ctx_.blit_image(BLPoint(curr_x, y - r.bearing_y), r.emoji_img);
            curr_x += r.width;
        } else {
            ctx_.fill_utf8_text(BLPoint(curr_x, y), font, r.text.data(), r.text.size());
            curr_x += r.width;
        }
    }
}

void Surface::draw_shadow_rounded_rect(
    double x, double y, double w, double h,
    double rx, double ry,
    double blur_radius, double spread,
    double offset_x, double offset_y,
    const Color& shadow_color
) {
    if (shadow_color.a == 0) return;

    int pad_x = 0, pad_y = 0;
    BLImage shadow_img = ShadowEngine::instance().get_or_render_rounded_shadow(
        w, h, rx, ry, blur_radius, spread, shadow_color, pad_x, pad_y
    );

    if (shadow_img.is_empty()) return;

    std::lock_guard<std::mutex> lock(mutex_);
    double dst_x = x + offset_x - pad_x;
    double dst_y = y + offset_y - pad_y;
    ctx_.blit_image(BLPoint(dst_x, dst_y), shadow_img);
}

void Surface::draw_card(
    double x, double y, double w, double h,
    double rx, double ry,
    const Color& bg_color,
    const Color& border_color,
    double border_width,
    double shadow_blur,
    double shadow_spread,
    double shadow_offset_x,
    double shadow_offset_y,
    const Color& shadow_color
) {
    // 1. Draw soft drop shadow
    if (shadow_color.a > 0 && shadow_blur >= 0.0) {
        draw_shadow_rounded_rect(x, y, w, h, rx, ry, shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, shadow_color);
    }

    std::lock_guard<std::mutex> lock(mutex_);

    // 2. Draw card background
    if (bg_color.a > 0) {
        ctx_.set_fill_style(bg_color.to_bl_rgba32());
        ctx_.fill_round_rect(BLRoundRect(x, y, w, h, rx, ry));
    }

    // 3. Draw border stroke
    if (border_color.a > 0 && border_width > 0.0) {
        ctx_.set_stroke_style(border_color.to_bl_rgba32());
        ctx_.set_stroke_width(border_width);
        ctx_.stroke_round_rect(BLRoundRect(x + border_width * 0.5, y + border_width * 0.5, w - border_width, h - border_width, std::max(0.0, rx - border_width * 0.5), std::max(0.0, ry - border_width * 0.5)));
    }
}

// -----------------------------------------------------------------------------
// Typography Measurement & Multi-line Wrapping
// -----------------------------------------------------------------------------

TextMetrics Surface::measure_text(
    const std::string& text,
    float font_size,
    const std::string& font_family,
    int weight,
    bool italic
) {
    TextMetrics tm_out;
    if (text.empty()) return tm_out;

    BLFont font = FontManager::instance().create_font(font_family, font_size, weight, italic);
    if (font.is_empty()) return tm_out;

    BLTextMetrics tm;
    BLGlyphBuffer gb;
    gb.set_utf8_text(text.data(), text.size());
    font.get_text_metrics(gb, tm);

    tm_out.advance_x = tm.advance.x;
    tm_out.width = (tm.advance.x > 0.0) ? tm.advance.x : (tm.bounding_box.x1 - tm.bounding_box.x0);
    tm_out.ascent = font.metrics().ascent;
    tm_out.descent = font.metrics().descent;
    tm_out.height = tm_out.ascent + tm_out.descent;
    return tm_out;
}

std::vector<std::string> Surface::break_lines(
    const std::string& text,
    double max_width,
    float font_size,
    const std::string& font_family,
    int weight,
    bool italic,
    bool truncate_ellipsis,
    int max_lines
) {
    std::vector<std::string> result;
    if (text.empty()) return result;

    if (max_width <= 0.0) {
        std::stringstream ss(text);
        std::string line;
        while (std::getline(ss, line)) {
            result.push_back(line);
            if (max_lines > 0 && static_cast<int>(result.size()) >= max_lines) break;
        }
        return result;
    }

    BLFont font = FontManager::instance().create_font(font_family, font_size, weight, italic);
    if (font.is_empty()) {
        result.push_back(text);
        return result;
    }

    auto get_width = [&](const std::string& s) -> double {
        if (s.empty()) return 0.0;
        BLTextMetrics tm;
        BLGlyphBuffer gb;
        gb.set_utf8_text(s.data(), s.size());
        font.get_text_metrics(gb, tm);
        return (tm.advance.x > 0.0) ? tm.advance.x : (tm.bounding_box.x1 - tm.bounding_box.x0);
    };

    std::stringstream text_stream(text);
    std::string paragraph;

    while (std::getline(text_stream, paragraph)) {
        if (paragraph.empty()) {
            result.push_back("");
            if (max_lines > 0 && static_cast<int>(result.size()) >= max_lines) break;
            continue;
        }

        std::stringstream word_stream(paragraph);
        std::string word;
        std::string current_line;

        while (word_stream >> word) {
            std::string test_line = current_line.empty() ? word : (current_line + " " + word);
            if (get_width(test_line) <= max_width) {
                current_line = std::move(test_line);
            } else {
                if (!current_line.empty()) {
                    if (max_lines > 0 && static_cast<int>(result.size()) + 1 >= max_lines && truncate_ellipsis) {
                        while (!current_line.empty() && get_width(current_line + "...") > max_width) {
                            current_line.pop_back();
                        }
                        result.push_back(current_line + "...");
                        return result;
                    }
                    result.push_back(current_line);
                    if (max_lines > 0 && static_cast<int>(result.size()) >= max_lines) {
                        return result;
                    }
                    current_line = word;
                } else {
                    result.push_back(word);
                    if (max_lines > 0 && static_cast<int>(result.size()) >= max_lines) {
                        return result;
                    }
                    current_line.clear();
                }
            }
        }
        if (!current_line.empty()) {
            if (max_lines > 0 && static_cast<int>(result.size()) + 1 >= max_lines && truncate_ellipsis && text_stream.good()) {
                while (!current_line.empty() && get_width(current_line + "...") > max_width) {
                    current_line.pop_back();
                }
                result.push_back(current_line + "...");
                return result;
            }
            result.push_back(current_line);
            if (max_lines > 0 && static_cast<int>(result.size()) >= max_lines) break;
        }
    }

    return result;
}

void Surface::draw_text_wrapped(
    const std::string& text,
    double x, double y,
    double max_width,
    float font_size,
    const std::string& font_family,
    const Color& color,
    int align,
    int weight,
    bool italic,
    double line_height_factor,
    bool truncate_ellipsis,
    int max_lines
) {
    if (text.empty()) return;
    std::vector<std::string> lines = break_lines(text, max_width, font_size, font_family, weight, italic, truncate_ellipsis, max_lines);
    double line_step = static_cast<double>(font_size) * line_height_factor;
    for (size_t i = 0; i < lines.size(); ++i) {
        draw_text(lines[i], x, y + static_cast<double>(i) * line_step, font_size, font_family, color, align, weight, italic);
    }
}

// -----------------------------------------------------------------------------
// Compound Widget Renderers
// -----------------------------------------------------------------------------

void Surface::draw_button(
    double x, double y, double w, double h,
    double rx, double ry,
    const Color& bg_color,
    const Color& border_color,
    double border_width,
    const Color& fg_color,
    const std::string& text,
    float font_size,
    const std::string& font_family,
    int weight,
    bool italic,
    double shadow_blur,
    double shadow_offset_y,
    const Color& shadow_color,
    const Color& focus_ring_color,
    double focus_ring_width,
    bool is_pressed
) {
    double press_offset = is_pressed ? 1.0 : 0.0;

    // 1. Drop shadow
    if (shadow_color.a > 0 && shadow_blur > 0.0 && !is_pressed) {
        draw_shadow_rounded_rect(x, y + shadow_offset_y, w, h, rx, ry, shadow_blur, 0.0, 0.0, 0.0, shadow_color);
    }

    // 2. Button container & border
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (bg_color.a > 0) {
            ctx_.set_fill_style(bg_color.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, y + press_offset, w, h, rx, ry));
        }

        if (border_color.a > 0 && border_width > 0.0) {
            ctx_.set_stroke_style(border_color.to_bl_rgba32());
            ctx_.set_stroke_width(border_width);
            ctx_.stroke_round_rect(BLRoundRect(
                x + border_width * 0.5,
                y + press_offset + border_width * 0.5,
                w - border_width,
                h - border_width,
                std::max(0.0, rx - border_width * 0.5),
                std::max(0.0, ry - border_width * 0.5)
            ));
        }

        // 3. Focus ring
        if (focus_ring_color.a > 0 && focus_ring_width > 0.0) {
            ctx_.set_stroke_style(focus_ring_color.to_bl_rgba32());
            ctx_.set_stroke_width(focus_ring_width);
            double fr_pad = 1.5;
            ctx_.stroke_round_rect(BLRoundRect(
                x - fr_pad,
                y + press_offset - fr_pad,
                w + fr_pad * 2.0,
                h + fr_pad * 2.0,
                rx + fr_pad,
                ry + fr_pad
            ));
        }
    }

    // 4. Centered Button Typography
    if (!text.empty()) {
        double text_x = x + w / 2.0;
        double text_y = y + h / 2.0 + static_cast<double>(font_size) * 0.35 + press_offset;
        draw_text(text, text_x, text_y, font_size, font_family, fg_color, 1 /* center */, weight, italic);
    }
}

void Surface::draw_switch(
    double x, double y, double w, double h,
    const Color& track_color,
    const Color& thumb_color,
    const Color& thumb_border_color,
    double progress_t,
    bool is_hovered,
    const Color& focus_ring_color,
    double focus_ring_width
) {
    double r = h / 2.0;
    double clamped_t = std::max(0.0, std::min(1.0, progress_t));

    // Track
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (track_color.a > 0) {
            ctx_.set_fill_style(track_color.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, y, w, h, r, r));
        }

        if (focus_ring_color.a > 0 && focus_ring_width > 0.0) {
            ctx_.set_stroke_style(focus_ring_color.to_bl_rgba32());
            ctx_.set_stroke_width(focus_ring_width);
            double fr_pad = 1.5;
            ctx_.stroke_round_rect(BLRoundRect(x - fr_pad, y - fr_pad, w + fr_pad * 2.0, h + fr_pad * 2.0, r + fr_pad, r + fr_pad));
        }
    }

    // Sliding Thumb
    double thumb_d = std::max(4.0, h - 6.0);
    double tr = thumb_d / 2.0;
    double min_cx = x + 3.0 + tr;
    double max_cx = x + w - 3.0 - tr;
    double thumb_cx = min_cx + (max_cx - min_cx) * clamped_t;
    double thumb_cy = y + h / 2.0;

    // Thumb shadow
    draw_shadow_rounded_rect(thumb_cx - tr, thumb_cy - tr + 1.0, thumb_d, thumb_d, tr, tr, 2.5, 0.0, 0.0, 1.0, Color(0, 0, 0, 45));

    {
        std::lock_guard<std::mutex> lock(mutex_);
        ctx_.set_fill_style(thumb_color.to_bl_rgba32());
        ctx_.fill_circle(BLCircle(thumb_cx, thumb_cy, tr));

        if (thumb_border_color.a > 0) {
            ctx_.set_stroke_style(thumb_border_color.to_bl_rgba32());
            ctx_.set_stroke_width(1.0);
            ctx_.stroke_circle(BLCircle(thumb_cx, thumb_cy, tr));
        }
    }
}

void Surface::draw_slider(
    double x, double y, double w, double h,
    const Color& track_bg,
    const Color& active_bg,
    const Color& thumb_color,
    const Color& thumb_border_color,
    double value_t,
    double track_thickness,
    double thumb_radius,
    bool is_hovered,
    bool is_dragging,
    const Color& focus_ring_color,
    double focus_ring_width
) {
    double clamped_val = std::max(0.0, std::min(1.0, value_t));
    double th = std::max(2.0, track_thickness);
    double track_y = y + (h - th) / 2.0;
    double track_rx = th / 2.0;

    {
        std::lock_guard<std::mutex> lock(mutex_);
        // Inactive track
        if (track_bg.a > 0) {
            ctx_.set_fill_style(track_bg.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, track_y, w, th, track_rx, track_rx));
        }

        // Active segment
        double active_w = w * clamped_val;
        if (active_bg.a > 0 && active_w > 0.0) {
            ctx_.set_fill_style(active_bg.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, track_y, active_w, th, track_rx, track_rx));
        }
    }

    // Thumb
    double thumb_cx = x + w * clamped_val;
    double thumb_cy = y + h / 2.0;
    double tr = std::max(3.0, thumb_radius);

    // Thumb shadow
    draw_shadow_rounded_rect(thumb_cx - tr, thumb_cy - tr + 1.0, tr * 2.0, tr * 2.0, tr, tr, 3.0, 0.0, 0.0, 1.0, Color(0, 0, 0, 40));

    {
        std::lock_guard<std::mutex> lock(mutex_);
        ctx_.set_fill_style(thumb_color.to_bl_rgba32());
        ctx_.fill_circle(BLCircle(thumb_cx, thumb_cy, tr));

        if (thumb_border_color.a > 0) {
            ctx_.set_stroke_style(thumb_border_color.to_bl_rgba32());
            ctx_.set_stroke_width(1.5);
            ctx_.stroke_circle(BLCircle(thumb_cx, thumb_cy, tr));
        }

        if (focus_ring_color.a > 0 && focus_ring_width > 0.0) {
            ctx_.set_stroke_style(focus_ring_color.to_bl_rgba32());
            ctx_.set_stroke_width(focus_ring_width);
            ctx_.stroke_circle(BLCircle(thumb_cx, thumb_cy, tr + 2.0));
        }
    }
}

void Surface::draw_progress_bar(
    double x, double y, double w, double h,
    double rx, double ry,
    const Color& track_bg,
    const Color& bar_bg,
    double progress_t,
    bool is_indeterminate,
    double phase_offset
) {
    std::lock_guard<std::mutex> lock(mutex_);
    // Track
    if (track_bg.a > 0) {
        ctx_.set_fill_style(track_bg.to_bl_rgba32());
        ctx_.fill_round_rect(BLRoundRect(x, y, w, h, rx, ry));
    }

    if (bar_bg.a == 0) return;

    if (is_indeterminate) {
        ctx_.save();
        ctx_.clip_to_rect(BLRect(x, y, w, h));
        double pill_w = w * 0.35;
        double shift = std::fmod(std::abs(phase_offset), 1.0);
        double pill_x = x + shift * (w + pill_w) - pill_w;
        ctx_.set_fill_style(bar_bg.to_bl_rgba32());
        ctx_.fill_round_rect(BLRoundRect(pill_x, y, pill_w, h, rx, ry));
        ctx_.restore();
    } else {
        double prog_w = w * std::max(0.0, std::min(1.0, progress_t));
        if (prog_w > 0.0) {
            ctx_.set_fill_style(bar_bg.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, y, prog_w, h, rx, ry));
        }
    }
}

void Surface::draw_checkbox(
    double x, double y, double size,
    double rx, double ry,
    const Color& box_bg,
    const Color& border_color,
    double border_width,
    const Color& check_color,
    bool is_checked,
    bool is_hovered,
    const Color& focus_ring_color,
    double focus_ring_width
) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        // Box fill
        if (box_bg.a > 0) {
            ctx_.set_fill_style(box_bg.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, y, size, size, rx, ry));
        }

        // Box border
        if (border_color.a > 0 && border_width > 0.0) {
            ctx_.set_stroke_style(border_color.to_bl_rgba32());
            ctx_.set_stroke_width(border_width);
            ctx_.stroke_round_rect(BLRoundRect(
                x + border_width * 0.5,
                y + border_width * 0.5,
                size - border_width,
                size - border_width,
                std::max(0.0, rx - border_width * 0.5),
                std::max(0.0, ry - border_width * 0.5)
            ));
        }

        // Focus ring
        if (focus_ring_color.a > 0 && focus_ring_width > 0.0) {
            ctx_.set_stroke_style(focus_ring_color.to_bl_rgba32());
            ctx_.set_stroke_width(focus_ring_width);
            double fr_pad = 1.5;
            ctx_.stroke_round_rect(BLRoundRect(x - fr_pad, y - fr_pad, size + fr_pad * 2.0, size + fr_pad * 2.0, rx + fr_pad, ry + fr_pad));
        }

        // Checkmark vector path
        if (is_checked && check_color.a > 0) {
            BLPath checkPath;
            checkPath.move_to(x + size * 0.22, y + size * 0.52);
            checkPath.line_to(x + size * 0.42, y + size * 0.72);
            checkPath.line_to(x + size * 0.78, y + size * 0.28);

            ctx_.set_stroke_style(check_color.to_bl_rgba32());
            ctx_.set_stroke_width(std::max(1.5, size * 0.13));
            ctx_.set_stroke_caps(BL_STROKE_CAP_ROUND);
            ctx_.set_stroke_join(BL_STROKE_JOIN_ROUND);
            ctx_.stroke_path(checkPath);
        }
    }
}

void Surface::execute_batch(const DrawBatch& batch) {
    for (const auto& op : batch.ops) {
        switch (op.type) {
            case DrawOpType::Clear:
                clear(op.c1);
                break;
            case DrawOpType::FillRect:
                fill_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.c1);
                break;
            case DrawOpType::StrokeRect:
                stroke_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.c1, op.d[4]);
                break;
            case DrawOpType::FillRoundedRect:
                fill_rounded_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.c1);
                break;
            case DrawOpType::StrokeRoundedRect:
                stroke_rounded_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.c1, op.d[6]);
                break;
            case DrawOpType::FillCircle:
                fill_circle(op.d[0], op.d[1], op.d[2], op.c1);
                break;
            case DrawOpType::StrokeCircle:
                stroke_circle(op.d[0], op.d[1], op.d[2], op.c1, op.d[3]);
                break;
            case DrawOpType::DrawLine:
                draw_line(op.d[0], op.d[1], op.d[2], op.d[3], op.c1, op.d[4]);
                break;
            case DrawOpType::DrawText:
                draw_text(op.str, op.d[0], op.d[1], static_cast<float>(op.d[2]), "default", op.c1, op.i1, op.i2, op.i3 != 0);
                break;
            case DrawOpType::DrawShadowRoundedRect:
                draw_shadow_rounded_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.d[6], op.d[7], 0, 0, op.c1);
                break;
            case DrawOpType::DrawCard:
                draw_card(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.c1, op.c2, op.d[6], op.d[7], 0, 0, 0, Color(0,0,0,0));
                break;
            case DrawOpType::Save:
                save();
                break;
            case DrawOpType::Restore:
                restore();
                break;
            case DrawOpType::Translate:
                translate(op.d[0], op.d[1]);
                break;
            case DrawOpType::Scale:
                scale(op.d[0], op.d[1]);
                break;
            case DrawOpType::Rotate:
                rotate(op.d[0]);
                break;
            case DrawOpType::ClipRect:
                clip_rect(op.d[0], op.d[1], op.d[2], op.d[3]);
                break;
            case DrawOpType::ClipRoundedRect:
                clip_rounded_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5]);
                break;
            case DrawOpType::ResetClip:
                reset_clip();
                break;
            default:
                break;
        }
    }
}

void Surface::flush() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.flush(BL_CONTEXT_FLUSH_SYNC);
}

void Surface::blit_to_photo(
    uintptr_t interp_addr,
    const std::string& photo_name,
    int dst_x,
    int dst_y
) {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.flush(BL_CONTEXT_FLUSH_SYNC);

    Tcl_Interp* interp = reinterpret_cast<Tcl_Interp*>(interp_addr);
    if (!interp) {
        throw nb::value_error("Invalid Tcl_Interp address");
    }

    Tk_PhotoHandle photoHandle = Tk_FindPhoto(interp, photo_name.c_str());
    if (!photoHandle) {
        throw nb::value_error(("Tk_FindPhoto failed: PhotoImage '" + photo_name + "' not found").c_str());
    }

    BLImageData imgData;
    image_.get_data(&imgData);

    Tk_PhotoImageBlock block;
    block.pixelPtr = static_cast<unsigned char*>(imgData.pixel_data);
    block.width = static_cast<int>(imgData.size.w);
    block.height = static_cast<int>(imgData.size.h);
    block.pitch = static_cast<int>(imgData.stride);
    block.pixelSize = 4;
    // PRGB32 in little endian memory format: [B, G, R, A]
    block.offset[0] = 2; // R
    block.offset[1] = 1; // G
    block.offset[2] = 0; // B
    block.offset[3] = 3; // A

    Tk_PhotoPutBlock(
        interp,
        photoHandle,
        &block,
        dst_x, dst_y,
        block.width, block.height,
        TK_PHOTO_COMPOSITE_SET
    );
}

uint8_t* Surface::data_ptr() {
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<uint8_t*>(imgData.pixel_data);
}

size_t Surface::stride() const {
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<size_t>(imgData.stride);
}

size_t Surface::size_in_bytes() const {
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<size_t>(imgData.stride * imgData.size.h);
}

} // namespace tkblend

// -----------------------------------------------------------------------------
// Nanobind Python Bindings
// -----------------------------------------------------------------------------

NB_MODULE(_tkblend, m) {
    m.doc() = "High-performance Blend2D vector engine and Tkinter photo blitter";

    // Blend composition operators
    m.attr("COMP_OP_SRC_OVER") = static_cast<int>(BL_COMP_OP_SRC_OVER);
    m.attr("COMP_OP_SRC_COPY") = static_cast<int>(BL_COMP_OP_SRC_COPY);
    m.attr("COMP_OP_SRC_IN")   = static_cast<int>(BL_COMP_OP_SRC_IN);
    m.attr("COMP_OP_SRC_OUT")  = static_cast<int>(BL_COMP_OP_SRC_OUT);
    m.attr("COMP_OP_SRC_ATOP") = static_cast<int>(BL_COMP_OP_SRC_ATOP);
    m.attr("COMP_OP_DST_OVER") = static_cast<int>(BL_COMP_OP_DST_OVER);
    m.attr("COMP_OP_DST_IN")   = static_cast<int>(BL_COMP_OP_DST_IN);
    m.attr("COMP_OP_DST_OUT")  = static_cast<int>(BL_COMP_OP_DST_OUT);
    m.attr("COMP_OP_DST_ATOP") = static_cast<int>(BL_COMP_OP_DST_ATOP);
    m.attr("COMP_OP_XOR")      = static_cast<int>(BL_COMP_OP_XOR);
    m.attr("COMP_OP_CLEAR")    = static_cast<int>(BL_COMP_OP_CLEAR);
    m.attr("COMP_OP_PLUS")     = static_cast<int>(BL_COMP_OP_PLUS);
    m.attr("COMP_OP_MULTIPLY") = static_cast<int>(BL_COMP_OP_MULTIPLY);
    m.attr("COMP_OP_SCREEN")   = static_cast<int>(BL_COMP_OP_SCREEN);
    m.attr("COMP_OP_OVERLAY")  = static_cast<int>(BL_COMP_OP_OVERLAY);
    m.attr("COMP_OP_DARKEN")   = static_cast<int>(BL_COMP_OP_DARKEN);
    m.attr("COMP_OP_LIGHTEN")  = static_cast<int>(BL_COMP_OP_LIGHTEN);

    // Gradient extend modes
    m.attr("EXTEND_PAD")     = static_cast<int>(BL_EXTEND_MODE_PAD);
    m.attr("EXTEND_REPEAT")  = static_cast<int>(BL_EXTEND_MODE_REPEAT);
    m.attr("EXTEND_REFLECT") = static_cast<int>(BL_EXTEND_MODE_REFLECT);

    // Color binding
    nb::class_<tkblend::Color>(m, "Color")
        .def(nb::init<uint8_t, uint8_t, uint8_t, uint8_t>(),
             nb::arg("r") = 0, nb::arg("g") = 0, nb::arg("b") = 0, nb::arg("a") = 255)
        .def_rw("r", &tkblend::Color::r)
        .def_rw("g", &tkblend::Color::g)
        .def_rw("b", &tkblend::Color::b)
        .def_rw("a", &tkblend::Color::a)
        .def_static("from_hex", &tkblend::Color::from_hex, nb::arg("hex"))
        .def_static("from_u32", &tkblend::Color::from_u32, nb::arg("argb"))
        .def("to_u32", &tkblend::Color::to_u32)
        .def("lighten", &tkblend::Color::lighten, nb::arg("factor"))
        .def("darken", &tkblend::Color::darken, nb::arg("factor"))
        .def("lerp", &tkblend::Color::lerp, nb::arg("other"), nb::arg("t"))
        .def("with_alpha", &tkblend::Color::with_alpha, nb::arg("new_a"))
        .def("with_alpha_f", &tkblend::Color::with_alpha_f, nb::arg("new_a"))
        .def("__repr__", [](const tkblend::Color& c) {
            std::ostringstream ss;
            ss << "Color(r=" << (int)c.r << ", g=" << (int)c.g
               << ", b=" << (int)c.b << ", a=" << (int)c.a << ")";
            return ss.str();
        });

    // Easing & Spring bindings
    nb::enum_<tkblend::EasingType>(m, "EasingType", nb::is_arithmetic())
        .value("Linear", tkblend::EasingType::Linear)
        .value("QuadIn", tkblend::EasingType::QuadIn)
        .value("QuadOut", tkblend::EasingType::QuadOut)
        .value("QuadInOut", tkblend::EasingType::QuadInOut)
        .value("CubicIn", tkblend::EasingType::CubicIn)
        .value("CubicOut", tkblend::EasingType::CubicOut)
        .value("CubicInOut", tkblend::EasingType::CubicInOut)
        .value("QuartIn", tkblend::EasingType::QuartIn)
        .value("QuartOut", tkblend::EasingType::QuartOut)
        .value("QuartInOut", tkblend::EasingType::QuartInOut)
        .value("SineIn", tkblend::EasingType::SineIn)
        .value("SineOut", tkblend::EasingType::SineOut)
        .value("SineInOut", tkblend::EasingType::SineInOut)
        .value("ExpoIn", tkblend::EasingType::ExpoIn)
        .value("ExpoOut", tkblend::EasingType::ExpoOut)
        .value("ExpoInOut", tkblend::EasingType::ExpoInOut)
        .value("CircIn", tkblend::EasingType::CircIn)
        .value("CircOut", tkblend::EasingType::CircOut)
        .value("CircInOut", tkblend::EasingType::CircInOut)
        .value("ElasticIn", tkblend::EasingType::ElasticIn)
        .value("ElasticOut", tkblend::EasingType::ElasticOut)
        .value("ElasticInOut", tkblend::EasingType::ElasticInOut)
        .value("BackIn", tkblend::EasingType::BackIn)
        .value("BackOut", tkblend::EasingType::BackOut)
        .value("BackInOut", tkblend::EasingType::BackInOut)
        .value("BounceIn", tkblend::EasingType::BounceIn)
        .value("BounceOut", tkblend::EasingType::BounceOut)
        .value("BounceInOut", tkblend::EasingType::BounceInOut)
        .export_values();

    m.def("ease", [](nb::object easing_type, double t) -> double {
        if (nb::isinstance<tkblend::EasingType>(easing_type)) {
            return tkblend::ease(static_cast<int>(nb::cast<tkblend::EasingType>(easing_type)), t);
        }
        return tkblend::ease(nb::cast<int>(easing_type), t);
    }, nb::arg("easing_type"), nb::arg("t"));

    m.def("spring", &tkblend::spring, nb::arg("t"), nb::arg("mass") = 1.0, nb::arg("stiffness") = 100.0, nb::arg("damping") = 10.0);

    // TextMetrics binding
    nb::class_<tkblend::TextMetrics>(m, "TextMetrics")
        .def_ro("width", &tkblend::TextMetrics::width)
        .def_ro("height", &tkblend::TextMetrics::height)
        .def_ro("ascent", &tkblend::TextMetrics::ascent)
        .def_ro("descent", &tkblend::TextMetrics::descent)
        .def_ro("advance_x", &tkblend::TextMetrics::advance_x)
        .def("__repr__", [](const tkblend::TextMetrics& tm) {
            std::ostringstream ss;
            ss << "TextMetrics(width=" << tm.width << ", height=" << tm.height
               << ", ascent=" << tm.ascent << ", descent=" << tm.descent
               << ", advance_x=" << tm.advance_x << ")";
            return ss.str();
        });

    // DrawBatch binding
    nb::class_<tkblend::DrawBatch>(m, "DrawBatch")
        .def(nb::init<>())
        .def("clear", &tkblend::DrawBatch::clear, nb::arg("color"))
        .def("fill_rect", &tkblend::DrawBatch::fill_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"))
        .def("stroke_rect", &tkblend::DrawBatch::stroke_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_rounded_rect", &tkblend::DrawBatch::fill_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("stroke_rounded_rect", &tkblend::DrawBatch::stroke_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_circle", &tkblend::DrawBatch::fill_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"))
        .def("stroke_circle", &tkblend::DrawBatch::stroke_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_line", &tkblend::DrawBatch::draw_line, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_text", &tkblend::DrawBatch::draw_text, nb::arg("text"), nb::arg("x"), nb::arg("y"), nb::arg("font_size") = 14.0f, nb::arg("font_family") = "default", nb::arg("color") = tkblend::Color(255, 255, 255, 255), nb::arg("align") = 0, nb::arg("weight") = 400, nb::arg("italic") = false)
        .def("draw_shadow_rounded_rect", &tkblend::DrawBatch::draw_shadow_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("blur_radius"), nb::arg("spread") = 0.0, nb::arg("offset_x") = 0.0, nb::arg("offset_y") = 0.0, nb::arg("shadow_color") = tkblend::Color(0, 0, 0, 128))
        .def("draw_card", &tkblend::DrawBatch::draw_card, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("bg_color"), nb::arg("border_color") = tkblend::Color(0, 0, 0, 0), nb::arg("border_width") = 0.0, nb::arg("shadow_blur") = 0.0, nb::arg("shadow_spread") = 0.0, nb::arg("shadow_offset_x") = 0.0, nb::arg("shadow_offset_y") = 0.0, nb::arg("shadow_color") = tkblend::Color(0, 0, 0, 0))
        .def("save", &tkblend::DrawBatch::save)
        .def("restore", &tkblend::DrawBatch::restore)
        .def("translate", &tkblend::DrawBatch::translate, nb::arg("tx"), nb::arg("ty"))
        .def("scale", &tkblend::DrawBatch::scale, nb::arg("sx"), nb::arg("sy"))
        .def("rotate", &tkblend::DrawBatch::rotate, nb::arg("rad"))
        .def("clip_rect", &tkblend::DrawBatch::clip_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("clip_rounded_rect", &tkblend::DrawBatch::clip_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"))
        .def("reset_clip", &tkblend::DrawBatch::reset_clip)
        .def("reset", &tkblend::DrawBatch::reset)
        .def("__len__", &tkblend::DrawBatch::size);

    // Gradient binding
    nb::class_<tkblend::Gradient>(m, "Gradient")
        .def_static("linear", &tkblend::Gradient::create_linear,
                    nb::arg("x0"), nb::arg("y0"), nb::arg("x1"), nb::arg("y1"))
        .def_static("radial", &tkblend::Gradient::create_radial,
                    nb::arg("x0"), nb::arg("y0"), nb::arg("r0"),
                    nb::arg("x1"), nb::arg("y1"), nb::arg("r1"))
        .def("add_stop", &tkblend::Gradient::add_stop, nb::arg("offset"), nb::arg("color"))
        .def("set_extend_mode", &tkblend::Gradient::set_extend_mode, nb::arg("mode"));

    // Path binding
    nb::class_<tkblend::Path>(m, "Path")
        .def(nb::init<>())
        .def("move_to", &tkblend::Path::move_to, nb::arg("x"), nb::arg("y"), nb::rv_policy::reference)
        .def("line_to", &tkblend::Path::line_to, nb::arg("x"), nb::arg("y"), nb::rv_policy::reference)
        .def("quad_to", &tkblend::Path::quad_to, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::rv_policy::reference)
        .def("cubic_to", &tkblend::Path::cubic_to, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("x3"), nb::arg("y3"), nb::rv_policy::reference)
        .def("arc_to", &tkblend::Path::arc_to, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("start_angle"), nb::arg("sweep_angle"), nb::rv_policy::reference)
        .def("add_rect", &tkblend::Path::add_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::rv_policy::reference)
        .def("add_rounded_rect", &tkblend::Path::add_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::rv_policy::reference)
        .def("add_circle", &tkblend::Path::add_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::rv_policy::reference)
        .def("add_ellipse", &tkblend::Path::add_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::rv_policy::reference)
        .def("close", &tkblend::Path::close, nb::rv_policy::reference)
        .def("clear", &tkblend::Path::clear, nb::rv_policy::reference)
        .def("reset", &tkblend::Path::reset, nb::rv_policy::reference);

    // FontManager bindings
    m.def("load_font_face", [](const std::string& name, const std::string& filepath) {
        return tkblend::FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("load_font", [](const std::string& name, const std::string& filepath) {
        return tkblend::FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("register_font", [](const std::string& name, const std::string& filepath) {
        return tkblend::FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("find_system_font", [](const std::string& family, int weight, bool italic) -> nb::object {
        std::string p = tkblend::FontManager::instance().find_system_font(family, weight, italic);
        if (p.empty()) {
            return nb::none();
        }
        return nb::str(p.c_str());
    }, nb::arg("family"), nb::arg("weight") = 400, nb::arg("italic") = false);

    m.def("get_loaded_fonts", []() {
        return tkblend::FontManager::instance().get_loaded_fonts();
    });

    m.def("get_internal_fonts", []() {
        return tkblend::FontManager::instance().get_loaded_fonts();
    });

    m.def("get_system_fonts", [](bool refresh) {
        return tkblend::FontManager::instance().get_system_fonts(refresh);
    }, nb::arg("refresh") = false);

    m.def("get_active_font", []() -> std::string {
        return tkblend::FontManager::instance().get_active_font();
    });

    m.def("set_active_font", [](const std::string& family_or_path) -> bool {
        return tkblend::FontManager::instance().set_active_font(family_or_path);
    }, nb::arg("family_or_path"));

    m.def("register_font_directory", [](const std::string& dir_path) {
        return tkblend::FontManager::instance().register_font_directory(dir_path);
    }, nb::arg("dir_path"));

    m.def("set_emoji_font", [](const std::string& path) {
        tkblend::EmojiEngine::instance().set_emoji_font(path);
    }, nb::arg("path"));

    m.def("get_emoji_font", []() -> std::string {
        return tkblend::EmojiEngine::instance().get_emoji_font_path();
    });

    // Surface binding
    nb::class_<tkblend::Surface>(m, "Surface")
        .def(nb::init<int, int>(), nb::arg("width"), nb::arg("height"))
        .def_prop_ro("width", &tkblend::Surface::width)
        .def_prop_ro("height", &tkblend::Surface::height)
        .def("resize", &tkblend::Surface::resize, nb::arg("width"), nb::arg("height"), nb::call_guard<nb::gil_scoped_release>())
        .def("clear", &tkblend::Surface::clear, nb::arg("color"))
        .def("clear_rect", &tkblend::Surface::clear_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("save", &tkblend::Surface::save)
        .def("restore", &tkblend::Surface::restore)
        .def("reset_transform", &tkblend::Surface::reset_transform)
        .def("translate", &tkblend::Surface::translate, nb::arg("tx"), nb::arg("ty"))
        .def("scale", &tkblend::Surface::scale, nb::arg("sx"), nb::arg("sy"))
        .def("rotate", &tkblend::Surface::rotate, nb::arg("angle_rad"))
        .def("clip_rect", &tkblend::Surface::clip_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("clip_rounded_rect", &tkblend::Surface::clip_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"))
        .def("reset_clip", &tkblend::Surface::reset_clip)
        .def("set_comp_op", &tkblend::Surface::set_comp_op, nb::arg("comp_op"))
        .def("set_global_alpha", &tkblend::Surface::set_global_alpha, nb::arg("alpha"))
        
        // Rectangles & Rounded Rectangles
        .def("fill_rect", &tkblend::Surface::fill_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"))
        .def("fill_rect_gradient", &tkblend::Surface::fill_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("gradient"))
        .def("stroke_rect", &tkblend::Surface::stroke_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_rounded_rect", &tkblend::Surface::fill_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("fill_rounded_rect_gradient", &tkblend::Surface::fill_rounded_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("gradient"))
        .def("stroke_rounded_rect", &tkblend::Surface::stroke_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Circles & Ellipses
        .def("fill_circle", &tkblend::Surface::fill_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"))
        .def("fill_circle_gradient", &tkblend::Surface::fill_circle_gradient, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("gradient"))
        .def("stroke_circle", &tkblend::Surface::stroke_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_ellipse", &tkblend::Surface::fill_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("stroke_ellipse", &tkblend::Surface::stroke_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Lines & Paths
        .def("draw_line", &tkblend::Surface::draw_line, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_path", &tkblend::Surface::fill_path, nb::arg("path"), nb::arg("color"))
        .def("fill_path_gradient", &tkblend::Surface::fill_path_gradient, nb::arg("path"), nb::arg("gradient"))
        .def("stroke_path", &tkblend::Surface::stroke_path, nb::arg("path"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Typography & Metrics
        .def("measure_text", [](tkblend::Surface& s,
                                const std::string& text, float font_size,
                                const std::string& font_family, int weight,
                                bool italic, bool bold) {
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            return s.measure_text(text, font_size, font_family, eff_weight, italic);
        },
             nb::arg("text"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false)

        .def("break_lines", [](tkblend::Surface& s,
                               const std::string& text, double max_width,
                               float font_size, const std::string& font_family,
                               int weight, bool italic, bool bold,
                               bool truncate_ellipsis, int max_lines) {
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            return s.break_lines(text, max_width, font_size, font_family, eff_weight, italic, truncate_ellipsis, max_lines);
        },
             nb::arg("text"), nb::arg("max_width"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("truncate_ellipsis") = false,
             nb::arg("max_lines") = 0)

        .def("draw_text", [](tkblend::Surface& s,
                             const std::string& text, double x, double y,
                             float font_size, const std::string& font_family,
                             std::optional<tkblend::Color> color, int align,
                             int weight, bool italic, bool bold) {
            tkblend::Color col = color.value_or(tkblend::Color(255, 255, 255, 255));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) {
                eff_weight = 700;
            }
            s.draw_text(text, x, y, font_size, font_family, col, align, eff_weight, italic);
        },
             nb::arg("text"), nb::arg("x"), nb::arg("y"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("color") = nb::none(),
             nb::arg("align") = 0,
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false)

        .def("draw_text_wrapped", [](tkblend::Surface& s,
                                     const std::string& text, double x, double y,
                                     double max_width, float font_size,
                                     const std::string& font_family,
                                     std::optional<tkblend::Color> color, int align,
                                     int weight, bool italic, bool bold,
                                     double line_height_factor, bool truncate_ellipsis,
                                     int max_lines) {
            tkblend::Color col = color.value_or(tkblend::Color(255, 255, 255, 255));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            s.draw_text_wrapped(text, x, y, max_width, font_size, font_family, col, align, eff_weight, italic, line_height_factor, truncate_ellipsis, max_lines);
        },
             nb::arg("text"), nb::arg("x"), nb::arg("y"), nb::arg("max_width"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("color") = nb::none(),
             nb::arg("align") = 0,
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("line_height_factor") = 1.25,
             nb::arg("truncate_ellipsis") = false,
             nb::arg("max_lines") = 0)

        // Shadows & Cards
        .def("draw_shadow_rounded_rect", [](tkblend::Surface& s,
                                            double x, double y, double w, double h,
                                            double rx, double ry,
                                            double blur_radius, double spread,
                                            double offset_x, double offset_y,
                                            std::optional<tkblend::Color> shadow_color) {
            tkblend::Color sc = shadow_color.value_or(tkblend::Color(0, 0, 0, 128));
            s.draw_shadow_rounded_rect(x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("blur_radius"), nb::arg("spread") = 0.0,
             nb::arg("offset_x") = 0.0, nb::arg("offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_card", [](tkblend::Surface& s,
                             double x, double y, double w, double h,
                             double rx, double ry,
                             const tkblend::Color& bg_color,
                             std::optional<tkblend::Color> border_color,
                             double border_width,
                             double shadow_blur,
                             double shadow_spread,
                             double shadow_offset_x,
                             double shadow_offset_y,
                             std::optional<tkblend::Color> shadow_color) {
            tkblend::Color bc = border_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color sc = shadow_color.value_or(tkblend::Color(0, 0, 0, 0));
            s.draw_card(x, y, w, h, rx, ry, bg_color, bc, border_width,
                        shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_spread") = 0.0,
             nb::arg("shadow_offset_x") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())

        // Compound Widgets
        .def("draw_button", [](tkblend::Surface& s,
                               double x, double y, double w, double h,
                               double rx, double ry,
                               const tkblend::Color& bg_color,
                               std::optional<tkblend::Color> border_color,
                               double border_width,
                               const tkblend::Color& fg_color,
                               const std::string& text,
                               float font_size,
                               const std::string& font_family,
                               int weight,
                               bool italic,
                               bool bold,
                               double shadow_blur,
                               double shadow_offset_y,
                               std::optional<tkblend::Color> shadow_color,
                               std::optional<tkblend::Color> focus_ring_color,
                               double focus_ring_width,
                               bool is_pressed) {
            tkblend::Color bc = border_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color sc = shadow_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color frc = focus_ring_color.value_or(tkblend::Color(0, 0, 0, 0));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            s.draw_button(x, y, w, h, rx, ry, bg_color, bc, border_width, fg_color,
                          text, font_size, font_family, eff_weight, italic,
                          shadow_blur, shadow_offset_y, sc, frc, focus_ring_width, is_pressed);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("fg_color") = tkblend::Color(255, 255, 255, 255),
             nb::arg("text") = "",
             nb::arg("font_size") = 13.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::arg("is_pressed") = false,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_switch", [](tkblend::Surface& s,
                              double x, double y, double w, double h,
                              const tkblend::Color& track_color,
                              const tkblend::Color& thumb_color,
                              std::optional<tkblend::Color> thumb_border_color,
                              double progress_t,
                              bool is_hovered,
                              std::optional<tkblend::Color> focus_ring_color,
                              double focus_ring_width) {
            tkblend::Color tbc = thumb_border_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color frc = focus_ring_color.value_or(tkblend::Color(0, 0, 0, 0));
            s.draw_switch(x, y, w, h, track_color, thumb_color, tbc, progress_t, is_hovered, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("track_color"),
             nb::arg("thumb_color"),
             nb::arg("thumb_border_color") = nb::none(),
             nb::arg("progress_t") = 0.0,
             nb::arg("is_hovered") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_slider", [](tkblend::Surface& s,
                              double x, double y, double w, double h,
                              const tkblend::Color& track_bg,
                              const tkblend::Color& active_bg,
                              const tkblend::Color& thumb_color,
                              std::optional<tkblend::Color> thumb_border_color,
                              double value_t,
                              double track_thickness,
                              double thumb_radius,
                              bool is_hovered,
                              bool is_dragging,
                              std::optional<tkblend::Color> focus_ring_color,
                              double focus_ring_width) {
            tkblend::Color tbc = thumb_border_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color frc = focus_ring_color.value_or(tkblend::Color(0, 0, 0, 0));
            s.draw_slider(x, y, w, h, track_bg, active_bg, thumb_color, tbc,
                          value_t, track_thickness, thumb_radius, is_hovered, is_dragging, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("track_bg"),
             nb::arg("active_bg"),
             nb::arg("thumb_color"),
             nb::arg("thumb_border_color") = nb::none(),
             nb::arg("value_t") = 0.0,
             nb::arg("track_thickness") = 4.0,
             nb::arg("thumb_radius") = 8.0,
             nb::arg("is_hovered") = false,
             nb::arg("is_dragging") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_progress_bar", &tkblend::Surface::draw_progress_bar,
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("track_bg"),
             nb::arg("bar_bg"),
             nb::arg("progress_t") = 0.0,
             nb::arg("is_indeterminate") = false,
             nb::arg("phase_offset") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_checkbox", [](tkblend::Surface& s,
                                double x, double y, double size,
                                double rx, double ry,
                                const tkblend::Color& box_bg,
                                std::optional<tkblend::Color> border_color,
                                double border_width,
                                const tkblend::Color& check_color,
                                bool is_checked,
                                bool is_hovered,
                                std::optional<tkblend::Color> focus_ring_color,
                                double focus_ring_width) {
            tkblend::Color bc = border_color.value_or(tkblend::Color(0, 0, 0, 0));
            tkblend::Color frc = focus_ring_color.value_or(tkblend::Color(0, 0, 0, 0));
            s.draw_checkbox(x, y, size, rx, ry, box_bg, bc, border_width, check_color, is_checked, is_hovered, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("size"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("box_bg"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("check_color") = tkblend::Color(255, 255, 255, 255),
             nb::arg("is_checked") = false,
             nb::arg("is_hovered") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        // Batch Execution
        .def("execute_batch", &tkblend::Surface::execute_batch,
             nb::arg("batch"),
             nb::call_guard<nb::gil_scoped_release>())

        // Tkinter Blit & Buffer
        .def("flush", &tkblend::Surface::flush, nb::call_guard<nb::gil_scoped_release>())
        .def("blit_to_photo", &tkblend::Surface::blit_to_photo,
             nb::arg("interp_addr"), nb::arg("photo_name"),
             nb::arg("dst_x") = 0, nb::arg("dst_y") = 0)
        .def("stride", &tkblend::Surface::stride)
        .def("size_in_bytes", &tkblend::Surface::size_in_bytes)
        
        .def("get_buffer", [](tkblend::Surface& s) -> nb::object {
            PyObject* mem = PyMemoryView_FromMemory(
                reinterpret_cast<char*>(s.data_ptr()),
                static_cast<Py_ssize_t>(s.size_in_bytes()),
                PyBUF_WRITE
            );
            if (!mem) {
                throw std::runtime_error("Failed to create memoryview from surface buffer");
            }
            return nb::steal(mem);
        });
}
