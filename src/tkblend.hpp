#pragma once

#include <blend2d.h>
#include <tcl.h>
#include <tk.h>

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <list>
#include <tuple>
#include <mutex>
#include <cmath>
#include <stdexcept>
#include <algorithm>

namespace tkblend {

// Color representation (RGBA 32-bit premultiplied or unpacked)
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

// Text Metrics & Typography Layout
struct TextMetrics {
    double width = 0.0;
    double height = 0.0;
    double ascent = 0.0;
    double descent = 0.0;
    double advance_x = 0.0;
};

struct TextLayoutOptions {
    double max_width = -1.0;
    double line_height_factor = 1.25;
    int align = 0; // 0=left, 1=center, 2=right
    bool wrap_words = true;
    bool truncate_ellipsis = false;
    int max_lines = 0;
};

// Easing curves
enum class EasingType {
    Linear = 0,
    QuadIn, QuadOut, QuadInOut,
    CubicIn, CubicOut, CubicInOut,
    QuartIn, QuartOut, QuartInOut,
    SineIn, SineOut, SineInOut,
    ExpoIn, ExpoOut, ExpoInOut,
    CircIn, CircOut, CircInOut,
    ElasticIn, ElasticOut, ElasticInOut,
    BackIn, BackOut, BackInOut,
    BounceIn, BounceOut, BounceInOut
};

double ease(int easing_type, double t);
double spring(double t, double mass = 1.0, double stiffness = 100.0, double damping = 10.0);

// Command Batch / Display List
enum class DrawOpType {
    Clear,
    FillRect, StrokeRect,
    FillRoundedRect, StrokeRoundedRect,
    FillCircle, StrokeCircle,
    FillEllipse, StrokeEllipse,
    DrawLine,
    DrawText,
    DrawShadowRoundedRect,
    DrawCard,
    Save, Restore, Translate, Scale, Rotate,
    ClipRect, ClipRoundedRect, ResetClip
};

struct DrawOp {
    DrawOpType type;
    double d[8] = {0};
    Color c1;
    Color c2;
    std::string str;
    int i1 = 0, i2 = 0, i3 = 0;
};

class DrawBatch {
public:
    std::vector<DrawOp> ops;

    void clear(const Color& c);
    void fill_rect(double x, double y, double w, double h, const Color& c);
    void stroke_rect(double x, double y, double w, double h, const Color& c, double stroke_width = 1.0);
    void fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c);
    void stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c, double stroke_width = 1.0);
    void fill_circle(double cx, double cy, double r, const Color& c);
    void stroke_circle(double cx, double cy, double r, const Color& c, double stroke_width = 1.0);
    void draw_line(double x1, double y1, double x2, double y2, const Color& c, double stroke_width = 1.0);
    void draw_text(const std::string& text, double x, double y, float font_size, const std::string& font_family, const Color& c, int align = 0, int weight = 400, bool italic = false);
    void draw_shadow_rounded_rect(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const Color& shadow_color);
    void draw_card(double x, double y, double w, double h, double rx, double ry, const Color& bg, const Color& border, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const Color& shadow_col);
    void save();
    void restore();
    void translate(double tx, double ty);
    void scale(double sx, double sy);
    void rotate(double rad);
    void clip_rect(double x, double y, double w, double h);
    void clip_rounded_rect(double x, double y, double w, double h, double rx, double ry);
    void reset_clip();
    void reset();
    size_t size() const { return ops.size(); }
};

// Gradient representation
class Gradient {
public:
    enum class Type { Linear, Radial };

    Type type = Type::Linear;
    // Linear coordinates: x0, y0, x1, y1
    // Radial coordinates: x0, y0, r0, x1, y1, r1
    double x0 = 0.0, y0 = 0.0;
    double x1 = 0.0, y1 = 0.0;
    double r0 = 0.0, r1 = 0.0;
    BLExtendMode extend_mode = BL_EXTEND_MODE_PAD;

    std::vector<std::pair<double, Color>> stops;

    static Gradient create_linear(double x0, double y0, double x1, double y1);
    static Gradient create_radial(double x0, double y0, double r0, double x1, double y1, double r1);

    void add_stop(double offset, const Color& color);
    void set_extend_mode(int mode);
    BLGradient to_bl_gradient() const;
};

// Path representation
class Path {
public:
    BLPath path;

    Path() = default;

    Path& move_to(double x, double y);
    Path& line_to(double x, double y);
    Path& quad_to(double x1, double y1, double x2, double y2);
    Path& cubic_to(double x1, double y1, double x2, double y2, double x3, double y3);
    Path& arc_to(double cx, double cy, double rx, double ry, double start_angle, double sweep_angle);
    Path& add_rect(double x, double y, double w, double h);
    Path& add_rounded_rect(double x, double y, double w, double h, double rx, double ry);
    Path& add_circle(double cx, double cy, double r);
    Path& add_ellipse(double cx, double cy, double rx, double ry);
    Path& close();
    Path& clear();
    Path& reset();
};

// Font Manager with system font discovery & typography control
class FontManager {
public:
    static FontManager& instance();

    bool load_font_face(const std::string& name, const std::string& filepath);
    std::string find_system_font(const std::string& family, int weight = 400, bool italic = false);
    std::vector<std::string> get_loaded_fonts();
    std::vector<std::string> get_system_fonts(bool refresh = false);
    int register_font_directory(const std::string& dir_path);

    std::string get_active_font() const;
    bool set_active_font(const std::string& family_or_path);

    BLFontFace* get_font_face(const std::string& family, int weight = 400, bool italic = false);
    BLFont create_font(const std::string& family, float size, int weight = 400, bool italic = false);

private:
    FontManager();
    std::string resolve_system_font_path(const std::string& family, int weight = 400, bool italic = false);

    std::unordered_map<std::string, BLFontFace> font_faces_;
    std::unordered_map<std::string, std::string> font_paths_;
    std::vector<std::string> system_fonts_cache_;
    std::string default_font_family_;
    mutable std::mutex mutex_;
};

// Fast Separable 3-Pass Box Blur & Shadow Engine
class ShadowEngine {
public:
    static ShadowEngine& instance();

    void apply_3pass_box_blur(BLImageData& data, double blur_radius);
    BLImage get_or_render_rounded_shadow(
        double w, double h, double rx, double ry,
        double blur_radius, double spread,
        const Color& shadow_color,
        int& out_pad_x, int& out_pad_y
    );

private:
    ShadowEngine() = default;

    struct ShadowKey {
        int w, h, rx, ry, blur_radius_10x, spread_10x;
        uint32_t color_u32;

        bool operator==(const ShadowKey& o) const {
            return w == o.w && h == o.h && rx == o.rx && ry == o.ry &&
                   blur_radius_10x == o.blur_radius_10x &&
                   spread_10x == o.spread_10x &&
                   color_u32 == o.color_u32;
        }
    };

    struct ShadowKeyHash {
        std::size_t operator()(const ShadowKey& k) const {
            std::size_t h1 = std::hash<int>()(k.w) ^ (std::hash<int>()(k.h) << 1);
            std::size_t h2 = std::hash<int>()(k.rx) ^ (std::hash<int>()(k.ry) << 1);
            std::size_t h3 = std::hash<int>()(k.blur_radius_10x) ^ (std::hash<int>()(k.spread_10x) << 1);
            std::size_t h4 = std::hash<uint32_t>()(k.color_u32);
            return h1 ^ (h2 << 2) ^ (h3 << 3) ^ (h4 << 4);
        }
    };

    struct CachedShadow {
        ShadowKey key;
        BLImage image;
        int pad_x = 0;
        int pad_y = 0;
    };

    std::list<CachedShadow> lru_list_;
    std::unordered_map<ShadowKey, std::list<CachedShadow>::iterator, ShadowKeyHash> cache_map_;
    const size_t max_cache_entries_ = 128;
    std::mutex mutex_;
};

// Emoji Engine powered by FreeType for color emoji rendering & font fallback
class EmojiEngine {
public:
    static EmojiEngine& instance();

    bool init();
    void set_emoji_font(const std::string& path);
    std::string get_emoji_font_path();

    static bool is_emoji(uint32_t codepoint);
    bool get_emoji_glyph(uint32_t codepoint, float target_size, BLImage& out_img, double& out_advance_x, double& out_bearing_y);

private:
    EmojiEngine();
    ~EmojiEngine();

    std::string resolve_system_emoji_font();

    struct GlyphKey {
        uint32_t codepoint;
        int size_int;

        bool operator==(const GlyphKey& o) const {
            return codepoint == o.codepoint && size_int == o.size_int;
        }
    };

    struct GlyphKeyHash {
        std::size_t operator()(const GlyphKey& k) const {
            return std::hash<uint32_t>()(k.codepoint) ^ (std::hash<int>()(k.size_int) << 16);
        }
    };

    struct CachedGlyph {
        BLImage image;
        double advance_x;
        double bearing_y;
        bool valid;
    };

    void* ft_lib_{nullptr};
    void* ft_face_{nullptr};
    std::string emoji_font_path_;
    std::unordered_map<GlyphKey, CachedGlyph, GlyphKeyHash> cache_;
    std::mutex mutex_;
    bool initialized_{false};
};

// Main Vector Drawing Surface
class Surface {
public:
    Surface(int width, int height);
    ~Surface();

    // Lifecycle & buffer sizing
    void resize(int width, int height);
    int width() const { return width_; }
    int height() const { return height_; }
    void clear(const Color& color);
    void clear_rect(double x, double y, double w, double h);

    // State management
    void save();
    void restore();
    void reset_transform();
    void translate(double tx, double ty);
    void scale(double sx, double sy);
    void rotate(double angle_rad);
    void clip_rect(double x, double y, double w, double h);
    void clip_rounded_rect(double x, double y, double w, double h, double rx, double ry);
    void reset_clip();
    void set_comp_op(int comp_op);
    void set_global_alpha(double alpha);

    // Basic Rectangles & Rounded Rectangles
    void fill_rect(double x, double y, double w, double h, const Color& color);
    void fill_rect_gradient(double x, double y, double w, double h, const Gradient& gradient);
    void stroke_rect(double x, double y, double w, double h, const Color& color, double stroke_width = 1.0);
    
    void fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color);
    void fill_rounded_rect_gradient(double x, double y, double w, double h, double rx, double ry, const Gradient& gradient);
    void stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color, double stroke_width = 1.0);

    // Circles & Ellipses
    void fill_circle(double cx, double cy, double r, const Color& color);
    void fill_circle_gradient(double cx, double cy, double r, const Gradient& gradient);
    void stroke_circle(double cx, double cy, double r, const Color& color, double stroke_width = 1.0);

    void fill_ellipse(double cx, double cy, double rx, double ry, const Color& color);
    void stroke_ellipse(double cx, double cy, double rx, double ry, const Color& color, double stroke_width = 1.0);

    // Lines & Paths
    void draw_line(double x1, double y1, double x2, double y2, const Color& color, double stroke_width = 1.0);
    void fill_path(const Path& path, const Color& color);
    void fill_path_gradient(const Path& path, const Gradient& gradient);
    void stroke_path(const Path& path, const Color& color, double stroke_width = 1.0);

    // Typography & Metrics
    TextMetrics measure_text(
        const std::string& text,
        float font_size = 14.0f,
        const std::string& font_family = "default",
        int weight = 400,
        bool italic = false
    );

    std::vector<std::string> break_lines(
        const std::string& text,
        double max_width,
        float font_size = 14.0f,
        const std::string& font_family = "default",
        int weight = 400,
        bool italic = false,
        bool truncate_ellipsis = false,
        int max_lines = 0
    );

    void draw_text(
        const std::string& text,
        double x, double y,
        float font_size,
        const std::string& font_family,
        const Color& color,
        int align = 0, // 0=left, 1=center, 2=right
        int weight = 400,
        bool italic = false
    );

    void draw_text_wrapped(
        const std::string& text,
        double x, double y,
        double max_width,
        float font_size,
        const std::string& font_family,
        const Color& color,
        int align = 0,
        int weight = 400,
        bool italic = false,
        double line_height_factor = 1.25,
        bool truncate_ellipsis = false,
        int max_lines = 0
    );

    // Modern Soft Shadows & Cards
    void draw_shadow_rounded_rect(
        double x, double y, double w, double h,
        double rx, double ry,
        double blur_radius, double spread,
        double offset_x, double offset_y,
        const Color& shadow_color
    );

    void draw_card(
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
    );

    // Specialized Compound Widgets
    void draw_button(
        double x, double y, double w, double h,
        double rx, double ry,
        const Color& bg_color,
        const Color& border_color,
        double border_width,
        const Color& fg_color,
        const std::string& text,
        float font_size = 13.0f,
        const std::string& font_family = "default",
        int weight = 400,
        bool italic = false,
        double shadow_blur = 0.0,
        double shadow_offset_y = 0.0,
        const Color& shadow_color = Color(0, 0, 0, 0),
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0,
        bool is_pressed = false
    );

    void draw_switch(
        double x, double y, double w, double h,
        const Color& track_color,
        const Color& thumb_color,
        const Color& thumb_border_color,
        double progress_t, // 0.0 = off, 1.0 = on
        bool is_hovered = false,
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0
    );

    void draw_slider(
        double x, double y, double w, double h,
        const Color& track_bg,
        const Color& active_bg,
        const Color& thumb_color,
        const Color& thumb_border_color,
        double value_t, // 0.0 - 1.0
        double track_thickness = 4.0,
        double thumb_radius = 8.0,
        bool is_hovered = false,
        bool is_dragging = false,
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0
    );

    void draw_progress_bar(
        double x, double y, double w, double h,
        double rx, double ry,
        const Color& track_bg,
        const Color& bar_bg,
        double progress_t, // 0.0 - 1.0
        bool is_indeterminate = false,
        double phase_offset = 0.0
    );

    void draw_checkbox(
        double x, double y, double size,
        double rx, double ry,
        const Color& box_bg,
        const Color& border_color,
        double border_width,
        const Color& check_color,
        bool is_checked,
        bool is_hovered = false,
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0
    );

    // Display List Execution
    void execute_batch(const DrawBatch& batch);

    // Tcl/Tk Blitting Bridge
    void blit_to_photo(
        uintptr_t interp_addr,
        const std::string& photo_name,
        int dst_x = 0,
        int dst_y = 0
    );

    void flush();

    // Raw Pixel buffer access
    uint8_t* data_ptr();
    size_t stride() const;
    size_t size_in_bytes() const;

private:
    void init_context();

    int width_ = 1;
    int height_ = 1;
    BLImage image_;
    BLContext ctx_;
    std::mutex mutex_;
};

} // namespace tkblend
