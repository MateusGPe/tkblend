#include "tkblend.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/pair.h>

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
    discover_system_fonts();
}

void FontManager::discover_system_fonts() {
    std::vector<std::string> priority_fonts = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/roboto/unhinted/Roboto-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/System/Library/Fonts/SFProText-Regular.otf",
        "/Library/Fonts/Arial.ttf"
    };

    for (const auto& pf : priority_fonts) {
        if (fs::exists(pf)) {
            font_paths_["sans-serif"] = pf;
            font_paths_["default"] = pf;
            default_font_family_ = "sans-serif";
            break;
        }
    }

    std::vector<std::string> search_dirs = {
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        "~/.local/share/fonts",
        "~/.fonts",
        "C:\\Windows\\Fonts",
        "/System/Library/Fonts",
        "/Library/Fonts"
    };

    auto register_font = [this](const std::string& key, const std::string& path) {
        if (font_paths_.find(key) == font_paths_.end() && fs::exists(path)) {
            font_paths_[key] = path;
            if (default_font_family_.empty()) {
                default_font_family_ = key;
            }
        }
    };

    for (const auto& d : search_dirs) {
        try {
            if (!fs::exists(d)) continue;
            for (const auto& entry : fs::recursive_directory_iterator(d, fs::directory_options::skip_permission_denied)) {
                if (entry.is_regular_file()) {
                    std::string ext = entry.path().extension().string();
                    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                    if (ext == ".ttf" || ext == ".otf" || ext == ".ttc") {
                        std::string stem = entry.path().stem().string();
                        std::string lower_stem = stem;
                        std::transform(lower_stem.begin(), lower_stem.end(), lower_stem.begin(), ::tolower);
                        
                        register_font(lower_stem, entry.path().string());
                        
                        if (lower_stem.find("dejavusans") != std::string::npos ||
                            lower_stem.find("liberationsans") != std::string::npos ||
                            lower_stem.find("roboto") != std::string::npos ||
                            lower_stem.find("ubuntu") != std::string::npos ||
                            lower_stem.find("segoeui") != std::string::npos ||
                            lower_stem.find("arial") != std::string::npos ||
                            lower_stem.find("sf-pro") != std::string::npos ||
                            lower_stem.find("inter") != std::string::npos) {
                            register_font("sans-serif", entry.path().string());
                            register_font("default", entry.path().string());
                        }
                    }
                }
            }
        } catch (...) {
            // Ignore directory scanning exceptions
        }
    }
}

bool FontManager::load_font_face(const std::string& name, const std::string& filepath) {
    std::lock_guard<std::mutex> lock(mutex_);
    BLFontFace face;
    BLResult result = face.create_from_file(filepath.c_str());
    if (result == BL_SUCCESS) {
        std::string lower_name = name;
        std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
        font_faces_[lower_name] = face;
        return true;
    }
    return false;
}

BLFontFace* FontManager::get_font_face(const std::string& family) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string lower_family = family;
    std::transform(lower_family.begin(), lower_family.end(), lower_family.begin(), ::tolower);

    if (lower_family.empty() || lower_family == "default") {
        lower_family = "sans-serif";
    }

    auto it = font_faces_.find(lower_family);
    if (it != font_faces_.end()) {
        return &it->second;
    }

    auto path_it = font_paths_.find(lower_family);
    if (path_it == font_paths_.end()) {
        path_it = font_paths_.find("sans-serif");
    }
    if (path_it == font_paths_.end() && !font_paths_.empty()) {
        path_it = font_paths_.begin();
    }

    if (path_it != font_paths_.end()) {
        BLFontFace face;
        BLResult res = face.create_from_file(path_it->second.c_str());
        if (res == BL_SUCCESS) {
            auto inserted = font_faces_.emplace(lower_family, face);
            return &inserted.first->second;
        }
    }

    return nullptr;
}

BLFont FontManager::create_font(const std::string& family, float size) {
    BLFontFace* face = get_font_face(family);
    BLFont font;
    if (face) {
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

void Surface::draw_text(
    const std::string& text,
    double x, double y,
    float font_size,
    const std::string& font_family,
    const Color& color,
    int align
) {
    std::lock_guard<std::mutex> lock(mutex_);
    BLFont font = FontManager::instance().create_font(font_family, font_size);
    if (font.is_empty()) return;

    double draw_x = x;
    double draw_y = y;

    if (align != 0) {
        BLTextMetrics tm;
        BLGlyphBuffer gb;
        gb.set_utf8_text(text.data(), text.size());
        font.get_text_metrics(gb, tm);
        double text_w = tm.bounding_box.x1 - tm.bounding_box.x0;
        if (align == 1) {
            draw_x -= text_w / 2.0;
        } else if (align == 2) {
            draw_x -= text_w;
        }
    }

    ctx_.set_fill_style(color.to_bl_rgba32());
    ctx_.fill_utf8_text(BLPoint(draw_x, draw_y), font, text.data(), text.size());
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
        .def("__repr__", [](const tkblend::Color& c) {
            std::ostringstream ss;
            ss << "Color(r=" << (int)c.r << ", g=" << (int)c.g
               << ", b=" << (int)c.b << ", a=" << (int)c.a << ")";
            return ss.str();
        });

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

    // FontManager binding
    m.def("load_font_face", [](const std::string& name, const std::string& filepath) {
        return tkblend::FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

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

        // Typography
        .def("draw_text", &tkblend::Surface::draw_text,
             nb::arg("text"), nb::arg("x"), nb::arg("y"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "sans-serif",
             nb::arg("color") = tkblend::Color(255, 255, 255, 255),
             nb::arg("align") = 0)

        // Shadows & Cards
        .def("draw_shadow_rounded_rect", &tkblend::Surface::draw_shadow_rounded_rect,
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("blur_radius"), nb::arg("spread") = 0.0,
             nb::arg("offset_x") = 0.0, nb::arg("offset_y") = 0.0,
             nb::arg("shadow_color") = tkblend::Color(0, 0, 0, 128),
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_card", &tkblend::Surface::draw_card,
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = tkblend::Color(0, 0, 0, 0),
             nb::arg("border_width") = 0.0,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_spread") = 0.0,
             nb::arg("shadow_offset_x") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = tkblend::Color(0, 0, 0, 0),
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
