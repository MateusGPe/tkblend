#include "surface.hpp"
#include "style_engine.hpp"
#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>

namespace tkblend {

Surface::Surface(int width, int height)
    : width_(std::max(1, width)), height_(std::max(1, height)) {
    init_context();
}

Surface::~Surface() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!is_closed_) {
        ctx_.end();
        image_.reset();
        is_closed_ = true;
    }
}

void Surface::close() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) return;
    if (active_buffers_.load(std::memory_order_relaxed) > 0) {
        throw std::runtime_error("Cannot close Surface while active buffer views exist");
    }
    ctx_.end();
    image_.reset();
    is_closed_ = true;
}

void Surface::init_context() {
    if (is_closed_) {
        throw std::runtime_error("Cannot re-initialize closed Surface");
    }
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
    if (is_closed_) {
        throw std::runtime_error("Cannot resize a closed Surface");
    }
    if (active_buffers_.load(std::memory_order_relaxed) > 0) {
        throw std::runtime_error("Cannot resize Surface while active buffer views exist");
    }
    width_ = w;
    height_ = h;
    init_context();
}

void Surface::clear(const Color& color) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot operate on a closed Surface");
    }
    if (color.a == 0) {
        ctx_.clear_all();
    } else {
        ctx_.set_fill_style(color.to_bl_rgba32());
        ctx_.fill_all();
    }
}

void Surface::clear_rect(double x, double y, double w, double h) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot operate on a closed Surface");
    }
    ctx_.clear_rect(BLRect(x, y, w, h));
}

void Surface::save() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot operate on a closed Surface");
    }
    ctx_.save();
}

void Surface::restore() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot operate on a closed Surface");
    }
    ctx_.restore();
}

void Surface::reset_transform() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot operate on a closed Surface");
    }
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
    // Blend2D BLContext currently only supports axis-aligned rectangular clipping natively.
    // We clip to the bounding rectangle of the rounded rect.
    (void)rx;
    (void)ry;
    ctx_.clip_to_rect(BLRect(x, y, w, h));
}

void Surface::reset_clip() {
    std::lock_guard<std::mutex> lock(mutex_);
    ctx_.restore_clipping();
}

void Surface::set_comp_op(int comp_op) {
    if (comp_op < 0 || comp_op >= static_cast<int>(BL_COMP_OP_MAX_VALUE)) {
        throw std::invalid_argument(
            "comp_op value " + std::to_string(comp_op) +
            " is out of valid BLCompOp range [0, " +
            std::to_string(static_cast<int>(BL_COMP_OP_MAX_VALUE) - 1) + "]");
    }
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

    // Fast check: does text contain any multibyte characters or characters requiring fallback?
    bool has_non_ascii = false;
    for (size_t i = 0; i < text.size(); ++i) {
        if (static_cast<unsigned char>(text[i]) >= 0x80) {
            has_non_ascii = true;
            break;
        }
    }

    if (!has_non_ascii) {
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

    // Rich text path with emoji and font fallback run-splitting
    enum class RunType { Text, FallbackFont, Emoji };
    struct TextRun {
        RunType type;
        std::string text;
        BLFont fallback_font;
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
            runs.push_back(TextRun{RunType::Text, cur_text, BLFont(), BLImage(), w, 0.0});
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
                runs.push_back(TextRun{RunType::Emoji, "", BLFont(), emoji_img, adv_x, bear_y});
                continue;
            }
        }

        // Check if primary font has glyph
        if (FontManager::font_has_glyph(font, cp)) {
            cur_text.append(prev_p, p - prev_p);
        } else {
            // Find fallback font
            BLFont fb = FontManager::instance().create_fallback_font_for_codepoint(cp, font_size, weight, italic);
            if (!fb.is_empty()) {
                flush_text();
                std::string fb_str(prev_p, p - prev_p);
                BLTextMetrics tm;
                BLGlyphBuffer gb;
                gb.set_utf8_text(fb_str.data(), fb_str.size());
                fb.get_text_metrics(gb, tm);
                double w = tm.advance.x;
                if (w <= 0.0) w = tm.bounding_box.x1 - tm.bounding_box.x0;
                if (w <= 0.0) w = font_size * 0.8;
                runs.push_back(TextRun{RunType::FallbackFont, fb_str, fb, BLImage(), w, 0.0});
            } else {
                cur_text.append(prev_p, p - prev_p);
            }
        }
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
        if (r.type == RunType::Emoji) {
            ctx_.blit_image(BLPoint(curr_x, y - r.bearing_y), r.emoji_img);
            curr_x += r.width;
        } else if (r.type == RunType::FallbackFont) {
            ctx_.fill_utf8_text(BLPoint(curr_x, y), r.fallback_font, r.text.data(), r.text.size());
            curr_x += r.width;
        } else {
            ctx_.fill_utf8_text(BLPoint(curr_x, y), font, r.text.data(), r.text.size());
            curr_x += r.width;
        }
    }
}

void Surface::draw_icon(
    const std::string& icon_char_or_name,
    double x, double y,
    float size,
    const Color& color,
    const std::string& font_family,
    int align
) {
    if (icon_char_or_name.empty()) return;
    std::string fam = font_family.empty() ? "fa-solid" : font_family;
    draw_text(icon_char_or_name, x, y, size, fam, color, align);
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

void Surface::render_box(
    double x, double y, double w, double h,
    const ComputedStyle& style,
    const std::string& text,
    int text_align
) {
    if (w <= 0.0 || h <= 0.0) return;

    // 1. Box drop-shadow rendering using ShadowEngine if shadow_color.a > 0 && shadow_blur > 0.0f
    if (style.shadow_color.a > 0 && style.shadow_blur > 0.0f) {
        draw_shadow_rounded_rect(
            x, y, w, h,
            style.border_radius, style.border_radius,
            style.shadow_blur, 0.0,
            style.shadow_offset_x, style.shadow_offset_y,
            style.shadow_color
        );
    }

    // 2. Background container fill (fill_rounded_rect)
    // 3. Border stroke (stroke_rounded_rect) inset by half stroke-width to avoid edge clipping
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (style.bg_color.a > 0) {
            ctx_.set_fill_style(style.bg_color.to_bl_rgba32());
            ctx_.fill_round_rect(BLRoundRect(x, y, w, h, style.border_radius, style.border_radius));
        }

        if (style.border_color.a > 0 && style.border_width > 0.0f) {
            ctx_.set_stroke_style(style.border_color.to_bl_rgba32());
            ctx_.set_stroke_width(style.border_width);
            double half_bw = style.border_width * 0.5;
            ctx_.stroke_round_rect(BLRoundRect(
                x + half_bw,
                y + half_bw,
                std::max(0.0, w - style.border_width),
                std::max(0.0, h - style.border_width),
                std::max(0.0, static_cast<double>(style.border_radius) - half_bw),
                std::max(0.0, static_cast<double>(style.border_radius) - half_bw)
            ));
        }
    }

    // 4. Antialiased text rendering with vertical centering
    if (!text.empty() && style.fg_color.a > 0) {
        double text_x = x;
        if (text_align == 1) { // center
            text_x = x + w / 2.0;
        } else if (text_align == 2) { // right
            text_x = x + w - 8.0;
        } else { // left
            text_x = x + 8.0;
        }
        double text_y = y + h / 2.0 + static_cast<double>(style.font_size) * 0.35;
        draw_text(text, text_x, text_y, style.font_size, style.font_family, style.fg_color, text_align, style.font_weight, false);
    }
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
        ctx_.stroke_round_rect(BLRoundRect(
            x + border_width * 0.5,
            y + border_width * 0.5,
            w - border_width,
            h - border_width,
            std::max(0.0, rx - border_width * 0.5),
            std::max(0.0, ry - border_width * 0.5)
        ));
    }
}

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
    (void)is_hovered;
    double r = h / 2.0;
    double clamped_t = std::clamp(progress_t, 0.0, 1.0);

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
    (void)is_hovered;
    (void)is_dragging;
    double clamped_val = std::clamp(value_t, 0.0, 1.0);
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
        double prog_w = w * std::clamp(progress_t, 0.0, 1.0);
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
    (void)is_hovered;
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
                draw_shadow_rounded_rect(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.d[6], op.d[7], op.d[8], op.d[9], op.c1);
                break;
            case DrawOpType::DrawCard:
                draw_card(op.d[0], op.d[1], op.d[2], op.d[3], op.d[4], op.d[5], op.c1, op.c2, op.d[6], op.d[7], op.d[8], op.d[9], op.d[10], op.c3);
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
    if (is_closed_) {
        throw std::runtime_error("Cannot blit from a closed Surface");
    }
    ctx_.flush(BL_CONTEXT_FLUSH_SYNC);

    Tcl_Interp* interp = reinterpret_cast<Tcl_Interp*>(interp_addr);
    if (!interp) {
        throw std::invalid_argument("Invalid Tcl_Interp address");
    }

    Tk_PhotoHandle photoHandle = Tk_FindPhoto(interp, photo_name.c_str());
    if (!photoHandle) {
        throw std::invalid_argument("Tk_FindPhoto failed: PhotoImage '" + photo_name + "' not found");
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

Surface::BufferViewInfo Surface::acquire_buffer_view() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_closed_) {
        throw std::runtime_error("Cannot acquire buffer view from a closed Surface");
    }
    active_buffers_.fetch_add(1, std::memory_order_relaxed);
    BLImageData imgData;
    image_.get_data(&imgData);
    return {
        static_cast<uint8_t*>(imgData.pixel_data),
        static_cast<size_t>(imgData.stride * imgData.size.h),
        static_cast<size_t>(imgData.stride)
    };
}

void Surface::release_buffer_view() {
    std::lock_guard<std::mutex> lock(mutex_);
    active_buffers_.fetch_sub(1, std::memory_order_relaxed);
}

uint8_t* Surface::data_ptr() {
    std::lock_guard<std::mutex> lock(mutex_);
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<uint8_t*>(imgData.pixel_data);
}

size_t Surface::stride() const {
    std::lock_guard<std::mutex> lock(mutex_);
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<size_t>(imgData.stride);
}

size_t Surface::size_in_bytes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    BLImageData imgData;
    image_.get_data(&imgData);
    return static_cast<size_t>(imgData.stride * imgData.size.h);
}

} // namespace tkblend
