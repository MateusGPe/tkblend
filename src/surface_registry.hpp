#pragma once

#include "surface.hpp"
#include "style_engine.hpp"

#include <cstdint>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <stdexcept>
#include <string>

namespace tkblend {

class SurfaceRegistry {
public:
    static SurfaceRegistry& instance() {
        static SurfaceRegistry reg;
        return reg;
    }

    uint64_t create_surface(int width, int height) {
        uint64_t id = next_id_.fetch_add(1, std::memory_order_relaxed);
        auto surf = std::make_unique<Surface>(width, height);
        std::lock_guard<std::mutex> lock(mutex_);
        surfaces_[id] = std::move(surf);
        return id;
    }

    Surface* get_surface(uint64_t id) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = surfaces_.find(id);
        if (it != surfaces_.end()) {
            return it->second.get();
        }
        return nullptr;
    }

    bool destroy_surface(uint64_t id) {
        std::unique_ptr<Surface> surf_to_destroy;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            auto it = surfaces_.find(id);
            if (it != surfaces_.end()) {
                surf_to_destroy = std::move(it->second);
                surfaces_.erase(it);
            }
        }
        if (surf_to_destroy) {
            surf_to_destroy->close();
            return true;
        }
        return false;
    }

    size_t active_surface_count() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return surfaces_.size();
    }

    void clear_all() {
        std::lock_guard<std::mutex> lock(mutex_);
        for (auto& [id, s] : surfaces_) {
            if (s) s->close();
        }
        surfaces_.clear();
    }

private:
    SurfaceRegistry() : next_id_(1) {}
    ~SurfaceRegistry() { clear_all(); }

    std::atomic<uint64_t> next_id_{1};
    mutable std::mutex mutex_;
    std::unordered_map<uint64_t, std::unique_ptr<Surface>> surfaces_;
};

class SurfaceHandle {
public:
    SurfaceHandle(int width, int height)
        : surface_id_(SurfaceRegistry::instance().create_surface(width, height)) {}

    ~SurfaceHandle() {
        if (surface_id_ != 0) {
            SurfaceRegistry::instance().destroy_surface(surface_id_);
            surface_id_ = 0;
        }
    }

    // Non-copyable, movable
    SurfaceHandle(const SurfaceHandle&) = delete;
    SurfaceHandle& operator=(const SurfaceHandle&) = delete;

    SurfaceHandle(SurfaceHandle&& other) noexcept : surface_id_(other.surface_id_) {
        other.surface_id_ = 0;
    }

    SurfaceHandle& operator=(SurfaceHandle&& other) noexcept {
        if (this != &other) {
            if (surface_id_ != 0) {
                SurfaceRegistry::instance().destroy_surface(surface_id_);
            }
            surface_id_ = other.surface_id_;
            other.surface_id_ = 0;
        }
        return *this;
    }

    uint64_t surface_id() const { return surface_id_; }

    Surface* get() const {
        return SurfaceRegistry::instance().get_surface(surface_id_);
    }

    Surface& surface() const {
        Surface* s = get();
        if (!s) throw std::runtime_error("SurfaceHandle references a destroyed or invalid Surface (ID=" + std::to_string(surface_id_) + ")");
        return *s;
    }

    int width() const { return surface().width(); }
    int height() const { return surface().height(); }
    bool is_closed() const {
        Surface* s = get();
        return s ? s->is_closed() : true;
    }

    void resize(int width, int height) {
        surface().resize(width, height);
    }

    void clear(const Color& color) {
        surface().clear(color);
    }

    void clear_rect(double x, double y, double w, double h) {
        surface().clear_rect(x, y, w, h);
    }

    void render_box(
        double x, double y, double w, double h,
        const ComputedStyle& style,
        const std::string& text = "",
        int text_align = 1
    ) {
        surface().render_box(x, y, w, h, style, text, text_align);
    }

    void blit_to_photo(
        uintptr_t interp_addr,
        const std::string& photo_name,
        int dst_x = 0,
        int dst_y = 0
    ) {
        surface().blit_to_photo(interp_addr, photo_name, dst_x, dst_y);
    }

    void close() {
        if (surface_id_ != 0) {
            SurfaceRegistry::instance().destroy_surface(surface_id_);
            surface_id_ = 0;
        }
    }

    // Forwarding Drawing Primitives
    void save() { surface().save(); }
    void restore() { surface().restore(); }
    void reset_transform() { surface().reset_transform(); }
    void translate(double tx, double ty) { surface().translate(tx, ty); }
    void scale(double sx, double sy) { surface().scale(sx, sy); }
    void rotate(double angle_rad) { surface().rotate(angle_rad); }
    void clip_rect(double x, double y, double w, double h) { surface().clip_rect(x, y, w, h); }
    void clip_rounded_rect(double x, double y, double w, double h, double rx, double ry) {
        surface().clip_rounded_rect(x, y, w, h, rx, ry);
    }
    void reset_clip() { surface().reset_clip(); }
    void set_comp_op(int comp_op) { surface().set_comp_op(comp_op); }
    void set_global_alpha(double alpha) { surface().set_global_alpha(alpha); }

    void fill_rect(double x, double y, double w, double h, const Color& color) {
        surface().fill_rect(x, y, w, h, color);
    }
    void fill_rect_gradient(double x, double y, double w, double h, const Gradient& gradient) {
        surface().fill_rect_gradient(x, y, w, h, gradient);
    }
    void stroke_rect(double x, double y, double w, double h, const Color& color, double stroke_width = 1.0) {
        surface().stroke_rect(x, y, w, h, color, stroke_width);
    }

    void fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color) {
        surface().fill_rounded_rect(x, y, w, h, rx, ry, color);
    }
    void fill_rounded_rect_gradient(double x, double y, double w, double h, double rx, double ry, const Gradient& gradient) {
        surface().fill_rounded_rect_gradient(x, y, w, h, rx, ry, gradient);
    }
    void stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& color, double stroke_width = 1.0) {
        surface().stroke_rounded_rect(x, y, w, h, rx, ry, color, stroke_width);
    }

    void fill_circle(double cx, double cy, double r, const Color& color) {
        surface().fill_circle(cx, cy, r, color);
    }
    void fill_circle_gradient(double cx, double cy, double r, const Gradient& gradient) {
        surface().fill_circle_gradient(cx, cy, r, gradient);
    }
    void stroke_circle(double cx, double cy, double r, const Color& color, double stroke_width = 1.0) {
        surface().stroke_circle(cx, cy, r, color, stroke_width);
    }

    void fill_ellipse(double cx, double cy, double rx, double ry, const Color& color) {
        surface().fill_ellipse(cx, cy, rx, ry, color);
    }
    void stroke_ellipse(double cx, double cy, double rx, double ry, const Color& color, double stroke_width = 1.0) {
        surface().stroke_ellipse(cx, cy, rx, ry, color, stroke_width);
    }

    void draw_line(double x1, double y1, double x2, double y2, const Color& color, double stroke_width = 1.0) {
        surface().draw_line(x1, y1, x2, y2, color, stroke_width);
    }
    void fill_path(const Path& path, const Color& color) {
        surface().fill_path(path, color);
    }
    void fill_path_gradient(const Path& path, const Gradient& gradient) {
        surface().fill_path_gradient(path, gradient);
    }
    void stroke_path(const Path& path, const Color& color, double stroke_width = 1.0) {
        surface().stroke_path(path, color, stroke_width);
    }

    TextMetrics measure_text(
        const std::string& text,
        float font_size = 14.0f,
        const std::string& font_family = "default",
        int weight = 400,
        bool italic = false
    ) {
        return surface().measure_text(text, font_size, font_family, weight, italic);
    }

    std::vector<std::string> break_lines(
        const std::string& text,
        double max_width,
        float font_size = 14.0f,
        const std::string& font_family = "default",
        int weight = 400,
        bool italic = false,
        bool truncate_ellipsis = false,
        int max_lines = 0
    ) {
        return surface().break_lines(text, max_width, font_size, font_family, weight, italic, truncate_ellipsis, max_lines);
    }

    void draw_text(
        const std::string& text,
        double x, double y,
        float font_size,
        const std::string& font_family,
        const Color& color,
        int align = 0,
        int weight = 400,
        bool italic = false
    ) {
        surface().draw_text(text, x, y, font_size, font_family, color, align, weight, italic);
    }

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
    ) {
        surface().draw_text_wrapped(text, x, y, max_width, font_size, font_family, color, align, weight, italic, line_height_factor, truncate_ellipsis, max_lines);
    }

    void draw_shadow_rounded_rect(
        double x, double y, double w, double h,
        double rx, double ry,
        double blur_radius, double spread,
        double offset_x, double offset_y,
        const Color& shadow_color
    ) {
        surface().draw_shadow_rounded_rect(x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, shadow_color);
    }

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
    ) {
        surface().draw_card(x, y, w, h, rx, ry, bg_color, border_color, border_width,
                            shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, shadow_color);
    }

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
    ) {
        surface().draw_button(x, y, w, h, rx, ry, bg_color, border_color, border_width,
                              fg_color, text, font_size, font_family, weight, italic,
                              shadow_blur, shadow_offset_y, shadow_color, focus_ring_color,
                              focus_ring_width, is_pressed);
    }

    void draw_switch(
        double x, double y, double w, double h,
        const Color& track_color,
        const Color& thumb_color,
        const Color& thumb_border_color,
        double progress_t,
        bool is_hovered = false,
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0
    ) {
        surface().draw_switch(x, y, w, h, track_color, thumb_color, thumb_border_color,
                              progress_t, is_hovered, focus_ring_color, focus_ring_width);
    }

    void draw_slider(
        double x, double y, double w, double h,
        const Color& track_bg,
        const Color& active_bg,
        const Color& thumb_color,
        const Color& thumb_border_color,
        double value_t,
        double track_thickness = 4.0,
        double thumb_radius = 8.0,
        bool is_hovered = false,
        bool is_dragging = false,
        const Color& focus_ring_color = Color(0, 0, 0, 0),
        double focus_ring_width = 0.0
    ) {
        surface().draw_slider(x, y, w, h, track_bg, active_bg, thumb_color, thumb_border_color,
                              value_t, track_thickness, thumb_radius, is_hovered, is_dragging,
                              focus_ring_color, focus_ring_width);
    }

    void draw_progress_bar(
        double x, double y, double w, double h,
        double rx, double ry,
        const Color& track_bg,
        const Color& bar_bg,
        double progress_t,
        bool is_indeterminate = false,
        double phase_offset = 0.0
    ) {
        surface().draw_progress_bar(x, y, w, h, rx, ry, track_bg, bar_bg, progress_t,
                                    is_indeterminate, phase_offset);
    }

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
    ) {
        surface().draw_checkbox(x, y, size, rx, ry, box_bg, border_color, border_width,
                                check_color, is_checked, is_hovered, focus_ring_color, focus_ring_width);
    }

    void execute_batch(const DrawBatch& batch) { surface().execute_batch(batch); }
    void flush() { surface().flush(); }

    Surface::BufferViewInfo acquire_buffer_view() { return surface().acquire_buffer_view(); }
    void release_buffer_view() { surface().release_buffer_view(); }
    size_t stride() const { return surface().stride(); }
    size_t size_in_bytes() const { return surface().size_in_bytes(); }
    int active_buffers() const { return surface().active_buffers(); }

private:
    uint64_t surface_id_{0};
};

} // namespace tkblend
