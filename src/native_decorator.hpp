#pragma once

#include "platform_compat.h"
#include "surface.hpp"
#include "color.hpp"
#include "blit/blit_backend.h"
#include "window_shape.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/tuple.h>

#include <string>
#include <memory>
#include <mutex>
#include <cstdint>
#include <optional>
#include <tuple>

namespace nb = nanobind;

namespace tkblend {

class NativeDecorator {
public:
    NativeDecorator(
        uintptr_t interp_addr,
        const std::string& parent_path,
        const std::string& widget_name,
        int width = 200,
        int height = 45
    );
    ~NativeDecorator();

    // Window Path and Status
    const std::string& path() const { return path_; }
    bool is_attached() const { return tkwin_ != nullptr; }
    const std::string& child_path() const { return child_path_; }

    // Child Attachment & Passive Monitoring
    bool attach_child(const std::string& child_path);
    void detach_child();

    // State properties
    bool is_focused() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return manual_focused_ || dec_focused_ || child_focused_;
    }
    void set_focused(bool focused);

    bool is_hovered() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return manual_hovered_ || dec_hovered_ || child_hovered_;
    }
    void set_hovered(bool hovered);

    // Geometry Negotiation
    void set_geometry_request(int width, int height);

    // Redraw Scheduling
    void request_redraw();

    // Insets calculation for children and boundaries (left, top, right, bottom)
    std::tuple<double, double, double, double> get_insets() const;

    // Child Window Shaping
    void update_child_shape();

    bool clip_child() const { std::lock_guard<std::mutex> lock(mutex_); return clip_child_; }
    void set_clip_child(bool clip);

    std::optional<double> child_rx() const { std::lock_guard<std::mutex> lock(mutex_); return child_rx_; }
    void set_child_rx(std::optional<double> val);

    std::optional<double> child_ry() const { std::lock_guard<std::mutex> lock(mutex_); return child_ry_; }
    void set_child_ry(std::optional<double> val);

    // Style Setters & Getters
    void set_style(
        std::optional<Color> bg_color = std::nullopt,
        std::optional<Color> hover_bg_color = std::nullopt,
        std::optional<Color> focus_bg_color = std::nullopt,
        std::optional<Color> parent_bg = std::nullopt,
        std::optional<Color> border_color = std::nullopt,
        std::optional<Color> border_hover_color = std::nullopt,
        std::optional<Color> border_focus_color = std::nullopt,
        std::optional<double> border_width = std::nullopt,
        std::optional<double> rx = std::nullopt,
        std::optional<double> ry = std::nullopt,
        std::optional<Color> shadow_color = std::nullopt,
        std::optional<double> shadow_blur = std::nullopt,
        std::optional<double> shadow_spread = std::nullopt,
        std::optional<double> shadow_offset_x = std::nullopt,
        std::optional<double> shadow_offset_y = std::nullopt,
        std::optional<bool> shadow_enabled = std::nullopt,
        std::optional<Color> focus_ring_color = std::nullopt,
        std::optional<double> focus_ring_width = std::nullopt,
        std::optional<double> focus_ring_offset = std::nullopt,
        std::optional<bool> clip_child = std::nullopt,
        std::optional<double> child_rx = std::nullopt,
        std::optional<double> child_ry = std::nullopt
    );

    Color bg_color() const { std::lock_guard<std::mutex> lock(mutex_); return bg_color_; }
    void set_bg_color(const Color& c) { { std::lock_guard<std::mutex> lock(mutex_); bg_color_ = c; } request_redraw(); }

    std::optional<Color> hover_bg_color() const { std::lock_guard<std::mutex> lock(mutex_); return hover_bg_color_; }
    void set_hover_bg_color(std::optional<Color> c) { { std::lock_guard<std::mutex> lock(mutex_); hover_bg_color_ = c; } request_redraw(); }

    std::optional<Color> focus_bg_color() const { std::lock_guard<std::mutex> lock(mutex_); return focus_bg_color_; }
    void set_focus_bg_color(std::optional<Color> c) { { std::lock_guard<std::mutex> lock(mutex_); focus_bg_color_ = c; } request_redraw(); }

    Color parent_bg() const { std::lock_guard<std::mutex> lock(mutex_); return parent_bg_; }
    void set_parent_bg(const Color& c) { { std::lock_guard<std::mutex> lock(mutex_); parent_bg_ = c; } request_redraw(); }

    Color border_color() const { std::lock_guard<std::mutex> lock(mutex_); return border_color_; }
    void set_border_color(const Color& c) { { std::lock_guard<std::mutex> lock(mutex_); border_color_ = c; } request_redraw(); }

    std::optional<Color> border_hover_color() const { std::lock_guard<std::mutex> lock(mutex_); return border_hover_color_; }
    void set_border_hover_color(std::optional<Color> c) { { std::lock_guard<std::mutex> lock(mutex_); border_hover_color_ = c; } request_redraw(); }

    std::optional<Color> border_focus_color() const { std::lock_guard<std::mutex> lock(mutex_); return border_focus_color_; }
    void set_border_focus_color(std::optional<Color> c) { { std::lock_guard<std::mutex> lock(mutex_); border_focus_color_ = c; } request_redraw(); }

    double border_width() const { std::lock_guard<std::mutex> lock(mutex_); return border_width_; }
    void set_border_width(double w) { { std::lock_guard<std::mutex> lock(mutex_); border_width_ = w; } update_child_shape(); request_redraw(); }

    double rx() const { std::lock_guard<std::mutex> lock(mutex_); return rx_; }
    void set_rx(double val) { { std::lock_guard<std::mutex> lock(mutex_); rx_ = val; } update_child_shape(); request_redraw(); }

    double ry() const { std::lock_guard<std::mutex> lock(mutex_); return ry_; }
    void set_ry(double val) { { std::lock_guard<std::mutex> lock(mutex_); ry_ = val; } update_child_shape(); request_redraw(); }

    Color shadow_color() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_color_; }
    void set_shadow_color(const Color& c) { { std::lock_guard<std::mutex> lock(mutex_); shadow_color_ = c; } request_redraw(); }

    double shadow_blur() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_blur_; }
    void set_shadow_blur(double b) { { std::lock_guard<std::mutex> lock(mutex_); shadow_blur_ = b; } request_redraw(); }

    double shadow_spread() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_spread_; }
    void set_shadow_spread(double s) { { std::lock_guard<std::mutex> lock(mutex_); shadow_spread_ = s; } request_redraw(); }

    double shadow_offset_x() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_offset_x_; }
    void set_shadow_offset_x(double x) { { std::lock_guard<std::mutex> lock(mutex_); shadow_offset_x_ = x; } request_redraw(); }

    double shadow_offset_y() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_offset_y_; }
    void set_shadow_offset_y(double y) { { std::lock_guard<std::mutex> lock(mutex_); shadow_offset_y_ = y; } request_redraw(); }

    bool shadow_enabled() const { std::lock_guard<std::mutex> lock(mutex_); return shadow_enabled_; }
    void set_shadow_enabled(bool enabled) { { std::lock_guard<std::mutex> lock(mutex_); shadow_enabled_ = enabled; } request_redraw(); }

    Color focus_ring_color() const { std::lock_guard<std::mutex> lock(mutex_); return focus_ring_color_; }
    void set_focus_ring_color(const Color& c) { { std::lock_guard<std::mutex> lock(mutex_); focus_ring_color_ = c; } request_redraw(); }

    double focus_ring_width() const { std::lock_guard<std::mutex> lock(mutex_); return focus_ring_width_; }
    void set_focus_ring_width(double w) { { std::lock_guard<std::mutex> lock(mutex_); focus_ring_width_ = w; } request_redraw(); }

    double focus_ring_offset() const { std::lock_guard<std::mutex> lock(mutex_); return focus_ring_offset_; }
    void set_focus_ring_offset(double o) { { std::lock_guard<std::mutex> lock(mutex_); focus_ring_offset_ = o; } request_redraw(); }

private:
    static void WindowEventHandler(ClientData clientData, XEvent* eventPtr);
    static void ChildEventHandler(ClientData clientData, XEvent* eventPtr);
    static void DisplayCallback(ClientData clientData);

    void on_window_event(XEvent* eventPtr);
    void on_child_event(XEvent* eventPtr);
    void render_and_present();
    void on_window_destroyed();

    Tk_Window tkwin_{nullptr};
    Tk_Window child_tkwin_{nullptr};
    Tcl_Interp* interp_{nullptr};
    std::string path_;
    std::string child_path_;

    std::unique_ptr<Surface> surface_;
    mutable std::mutex mutex_;

    bool redraw_pending_{false};
    bool manual_focused_{false};
    bool manual_hovered_{false};
    bool dec_focused_{false};
    bool child_focused_{false};
    bool dec_hovered_{false};
    bool child_hovered_{false};

    // Child shaping
    bool clip_child_{false};
    std::optional<double> child_rx_{std::nullopt};
    std::optional<double> child_ry_{std::nullopt};
    bool child_is_shaped_{false};

    // Styling properties
    Color bg_color_{255, 255, 255, 255};
    std::optional<Color> hover_bg_color_{std::nullopt};
    std::optional<Color> focus_bg_color_{std::nullopt};
    Color parent_bg_{0, 0, 0, 0};

    Color border_color_{200, 200, 200, 255};
    std::optional<Color> border_hover_color_{std::nullopt};
    std::optional<Color> border_focus_color_{std::nullopt};
    double border_width_{1.0};

    double rx_{8.0};
    double ry_{8.0};

    Color shadow_color_{0, 0, 0, 30};
    double shadow_blur_{8.0};
    double shadow_spread_{0.0};
    double shadow_offset_x_{0.0};
    double shadow_offset_y_{2.0};
    bool shadow_enabled_{true};

    Color focus_ring_color_{66, 133, 244, 255};
    double focus_ring_width_{2.0};
    double focus_ring_offset_{2.0};
};

} // namespace tkblend
