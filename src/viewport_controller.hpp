#pragma once

#include <tuple>
#include <algorithm>
#include <cmath>
#include <cstddef>

namespace tkblend {

struct ScrollbarLayoutResult {
    bool is_needed = false;
    double thumb_offset = 0.0;
    double thumb_len = 0.0;
    double track_len = 0.0;
    double max_scroll = 0.0;
};

class NativeViewportController {
public:
    NativeViewportController() = default;

    // Pure mathematical calculations
    static ScrollbarLayoutResult compute_scrollbar_geometry(
        double viewport_len,
        double content_len,
        double scroll_pos,
        double track_pad = 8.0,
        double min_thumb_len = 24.0,
        double min_track_len = 10.0
    );

    static double compute_scroll_drag_delta(
        double drag_delta_px,
        double max_scroll,
        double track_len,
        double thumb_len
    );

    static double compute_scroll_jump(
        double click_offset_in_track,
        double track_len,
        double max_scroll
    );

    static std::pair<size_t, size_t> compute_visible_range(
        double scroll_pos,
        double viewport_len,
        double item_len,
        size_t total_items,
        double header_offset = 0.0
    );

    // Stateful 2D viewport management
    void set_viewport_size(double w, double h);
    void set_content_size(double w, double h);
    void scroll_to(double x, double y);
    void scroll_by(double dx, double dy);

    double scroll_x() const { return scroll_x_; }
    double scroll_y() const { return scroll_y_; }
    double viewport_w() const { return viewport_w_; }
    double viewport_h() const { return viewport_h_; }
    double content_w() const { return content_w_; }
    double content_h() const { return content_h_; }

    ScrollbarLayoutResult vertical_scrollbar(double track_pad = 8.0, double min_thumb = 24.0, double min_track = 10.0) const;
    ScrollbarLayoutResult horizontal_scrollbar(double track_pad = 8.0, double min_thumb = 24.0, double min_track = 10.0) const;

    // Physics step (returns true if motion continues)
    bool step_physics(double dt, double friction = 0.92);

private:
    void clamp_scroll();

    double viewport_w_ = 0.0;
    double viewport_h_ = 0.0;
    double content_w_ = 0.0;
    double content_h_ = 0.0;

    double scroll_x_ = 0.0;
    double scroll_y_ = 0.0;
    double vel_x_ = 0.0;
    double vel_y_ = 0.0;
};

} // namespace tkblend
