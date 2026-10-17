#include "viewport_controller.hpp"

namespace tkblend {

ScrollbarLayoutResult NativeViewportController::compute_scrollbar_geometry(
    double viewport_len,
    double content_len,
    double scroll_pos,
    double track_pad,
    double min_thumb_len,
    double min_track_len
) {
    ScrollbarLayoutResult res;
    if (viewport_len <= 0.0 || content_len <= viewport_len) {
        return res;
    }

    res.is_needed = true;
    res.track_len = std::max(min_track_len, viewport_len - track_pad);
    double calculated_thumb = viewport_len * (viewport_len / content_len);
    res.thumb_len = std::min(res.track_len, std::max(min_thumb_len, calculated_thumb));
    res.max_scroll = std::max(1.0, content_len - viewport_len);

    double progress = std::clamp(scroll_pos / res.max_scroll, 0.0, 1.0);
    res.thumb_offset = progress * (res.track_len - res.thumb_len);
    return res;
}

double NativeViewportController::compute_scroll_drag_delta(
    double drag_delta_px,
    double max_scroll,
    double track_len,
    double thumb_len
) {
    double available_track = std::max(1.0, track_len - thumb_len);
    return drag_delta_px * (max_scroll / available_track);
}

double NativeViewportController::compute_scroll_jump(
    double click_offset_in_track,
    double track_len,
    double max_scroll
) {
    double click_ratio = std::clamp(click_offset_in_track / std::max(1.0, track_len), 0.0, 1.0);
    return click_ratio * max_scroll;
}

std::pair<size_t, size_t> NativeViewportController::compute_visible_range(
    double scroll_pos,
    double viewport_len,
    double item_len,
    size_t total_items,
    double header_offset
) {
    if (total_items == 0 || item_len <= 0.0 || viewport_len <= 0.0) {
        return {0, 0};
    }

    double adj_scroll = std::max(0.0, scroll_pos - header_offset);
    size_t first = static_cast<size_t>(std::max(0.0, std::floor(adj_scroll / item_len)));
    if (first >= total_items) {
        first = total_items > 0 ? total_items - 1 : 0;
    }

    double visible_bottom = adj_scroll + viewport_len;
    size_t last = static_cast<size_t>(std::ceil(visible_bottom / item_len)) + 1;
    if (last > total_items) {
        last = total_items;
    }

    return {first, last};
}

void NativeViewportController::set_viewport_size(double w, double h) {
    viewport_w_ = std::max(0.0, w);
    viewport_h_ = std::max(0.0, h);
    clamp_scroll();
}

void NativeViewportController::set_content_size(double w, double h) {
    content_w_ = std::max(0.0, w);
    content_h_ = std::max(0.0, h);
    clamp_scroll();
}

void NativeViewportController::scroll_to(double x, double y) {
    scroll_x_ = x;
    scroll_y_ = y;
    vel_x_ = 0.0;
    vel_y_ = 0.0;
    clamp_scroll();
}

void NativeViewportController::scroll_by(double dx, double dy) {
    scroll_x_ += dx;
    scroll_y_ += dy;
    clamp_scroll();
}

void NativeViewportController::clamp_scroll() {
    double max_x = std::max(0.0, content_w_ - viewport_w_);
    double max_y = std::max(0.0, content_h_ - viewport_h_);
    scroll_x_ = std::clamp(scroll_x_, 0.0, max_x);
    scroll_y_ = std::clamp(scroll_y_, 0.0, max_y);
}

ScrollbarLayoutResult NativeViewportController::vertical_scrollbar(double track_pad, double min_thumb, double min_track) const {
    return compute_scrollbar_geometry(viewport_h_, content_h_, scroll_y_, track_pad, min_thumb, min_track);
}

ScrollbarLayoutResult NativeViewportController::horizontal_scrollbar(double track_pad, double min_thumb, double min_track) const {
    return compute_scrollbar_geometry(viewport_w_, content_w_, scroll_x_, track_pad, min_thumb, min_track);
}

bool NativeViewportController::step_physics(double dt, double friction) {
    if (std::abs(vel_x_) < 0.05 && std::abs(vel_y_) < 0.05) {
        vel_x_ = 0.0;
        vel_y_ = 0.0;
        return false;
    }

    scroll_x_ += vel_x_ * dt;
    scroll_y_ += vel_y_ * dt;
    clamp_scroll();

    vel_x_ *= std::pow(friction, dt * 60.0);
    vel_y_ *= std::pow(friction, dt * 60.0);

    return true;
}

} // namespace tkblend
