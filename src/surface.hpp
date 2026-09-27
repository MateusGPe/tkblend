#pragma once

#include "color.hpp"
#include "gradient.hpp"
#include "path.hpp"
#include "font_manager.hpp"
#include "shadow_engine.hpp"
#include "emoji_engine.hpp"
#include "draw_batch.hpp"

#include <blend2d.h>
#include <tcl.h>
#include <tk.h>

#include <cstdint>
#include <string>
#include <vector>
#include <mutex>
#include <atomic>

namespace tkblend {

struct ComputedStyle;

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

// Main Vector Drawing Surface
class Surface {
public:
    Surface(int width, int height);
    ~Surface();

    // Lifecycle & buffer sizing
    void resize(int width, int height);
    void close();
    bool is_closed() const { return is_closed_; }
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

    // High-Level Declarative Box Painter
    void render_box(
        double x, double y, double w, double h,
        const ComputedStyle& style,
        const std::string& text = "",
        int text_align = 1 // 0=left, 1=center, 2=right
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
    struct BufferViewInfo {
        uint8_t* data = nullptr;
        size_t size = 0;
        size_t stride = 0;
    };

    BufferViewInfo acquire_buffer_view();
    void release_buffer_view();

    uint8_t* data_ptr();
    size_t stride() const;
    size_t size_in_bytes() const;
    void inc_active_buffers() { active_buffers_.fetch_add(1, std::memory_order_relaxed); }
    void dec_active_buffers() { active_buffers_.fetch_sub(1, std::memory_order_relaxed); }
    int active_buffers() const { return active_buffers_.load(std::memory_order_relaxed); }

private:
    void init_context();

    int width_ = 1;
    int height_ = 1;
    BLImage image_;
    BLContext ctx_;
    mutable std::mutex mutex_;
    std::atomic<int> active_buffers_{0};
    bool is_closed_{false};
};

} // namespace tkblend
