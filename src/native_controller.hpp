#pragma once

#include "platform_compat.h"
#include "surface.hpp"
#include "surface_registry.hpp"
#include "style_engine.hpp"
#include "blit/blit_backend.h"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/optional.h>

#include <string>
#include <memory>
#include <mutex>
#include <cstdint>

namespace nb = nanobind;

namespace tkblend {

enum class WidgetKind : uint8_t {
    Custom = 0,
    Box,
    Button,
    Badge,
    Checkbox,
    Radio,
    Switch,
    Slider,
    Progress,
    Separator
};

class NativeWidgetController {
public:
    NativeWidgetController();
    ~NativeWidgetController();

    // Attach / Detach native Tk window event handler
    bool attach(uintptr_t interp_addr, const std::string& widget_path);
    void detach();
    bool is_attached() const { return tkwin_ != nullptr; }

    // Redraw scheduling & Direct presentation
    void request_redraw();
    void blit_handle(SurfaceHandle& handle);
    void blit_surface(Surface& surf);
    void paint_and_blit();

    // Geometry negotiation
    void set_geometry_request(int req_w, int req_h);

    // Surface access
    Surface& surface() { return *surface_; }
    int width() const { return surface_->width(); }
    int height() const { return surface_->height(); }

    // State & Interactive Properties
    uint16_t state() const { return state_; }
    void set_state(uint16_t s) { state_ = s; }

    void set_auto_hover(bool enable) { auto_hover_ = enable; }
    bool auto_hover() const { return auto_hover_; }

    void set_auto_press(bool enable) { auto_press_ = enable; }
    bool auto_press() const { return auto_press_; }

    // Styling & Component Properties
    WidgetKind kind() const { return kind_; }
    void set_kind(WidgetKind k) { kind_ = k; }

    const std::string& element() const { return element_; }
    void set_element(const std::string& e) { element_ = e; }

    const std::string& class_name() const { return class_name_; }
    void set_class_name(const std::string& c) { class_name_ = c; }

    double scale() const { return scale_; }
    void set_scale(double s) { scale_ = s > 0.0 ? s : 1.0; }

    const std::string& text() const { return text_; }
    void set_text(const std::string& t) { text_ = t; }

    int text_align() const { return text_align_; }
    void set_text_align(int a) { text_align_ = a; }

    const Color& parent_bg() const { return parent_bg_; }
    void set_parent_bg(const Color& c) { parent_bg_ = c; }

    std::optional<Color> explicit_bg() const { return explicit_bg_; }
    void set_explicit_bg(std::optional<Color> c) { explicit_bg_ = c; }

    std::optional<Color> explicit_fg() const { return explicit_fg_; }
    void set_explicit_fg(std::optional<Color> c) { explicit_fg_ = c; }

    std::optional<Color> explicit_border() const { return explicit_border_; }
    void set_explicit_border(std::optional<Color> c) { explicit_border_ = c; }

    std::optional<double> custom_rx() const { return custom_rx_; }
    void set_custom_rx(std::optional<double> rx) { custom_rx_ = rx; }

    std::optional<double> custom_ry() const { return custom_ry_; }
    void set_custom_ry(std::optional<double> ry) { custom_ry_ = ry; }

    double elevation() const { return elevation_; }
    void set_elevation(double el) { elevation_ = el; }

    // Typography
    const std::string& font_family() const { return font_family_; }
    void set_font_family(const std::string& f) { font_family_ = f; }

    float font_size() const { return font_size_; }
    void set_font_size(float sz) { font_size_ = sz; }

    int font_weight() const { return font_weight_; }
    void set_font_weight(int w) { font_weight_ = w; }

    // Specific parameters
    bool is_checked() const { return is_checked_; }
    void set_is_checked(bool chk) { is_checked_ = chk; }

    double progress_t() const { return progress_t_; }
    void set_progress_t(double t) { progress_t_ = t; }

    double value_t() const { return value_t_; }
    void set_value_t(double t) { value_t_ = t; }

    bool is_indeterminate() const { return is_indeterminate_; }
    void set_is_indeterminate(bool ind) { is_indeterminate_ = ind; }

    double phase_offset() const { return phase_offset_; }
    void set_phase_offset(double ph) { phase_offset_ = ph; }

    bool dot() const { return dot_; }
    void set_dot(bool d) { dot_ = d; }

    std::optional<Color> dot_color() const { return dot_color_; }
    void set_dot_color(std::optional<Color> c) { dot_color_ = c; }

    // Safe Python Callback Stubs
    void set_on_paint(nb::object callback) {}
    void clear_on_paint() {}

    void set_on_state_changed(nb::object callback) {}
    void clear_on_state_changed() {}

    void set_on_click(nb::object callback) {}
    void clear_on_click() {}

private:
    static void HandleTkEvent(ClientData clientData, XEvent* eventPtr);
    static void IdleRedraw(ClientData clientData);

    void on_tk_event(XEvent* eventPtr);
    void blit_bound_surface();

    Tk_Window tkwin_{nullptr};
    Tcl_Interp* interp_{nullptr};
    std::string widget_path_;

    std::unique_ptr<Surface> surface_;
    uint64_t bound_surface_id_{0};
    mutable std::mutex mutex_;

    bool idle_scheduled_{false};
    bool auto_hover_{true};
    bool auto_press_{true};

    // State & Rendering Configuration
    uint16_t state_{0};
    WidgetKind kind_{WidgetKind::Box};
    std::string element_{"widget"};
    std::string class_name_;
    double scale_{1.0};
    std::string text_;
    int text_align_{1};

    Color parent_bg_{0, 0, 0, 0};
    std::optional<Color> explicit_bg_{std::nullopt};
    std::optional<Color> explicit_fg_{std::nullopt};
    std::optional<Color> explicit_border_{std::nullopt};
    std::optional<double> custom_rx_{std::nullopt};
    std::optional<double> custom_ry_{std::nullopt};
    double elevation_{0.0};

    std::string font_family_{"default"};
    float font_size_{0.0f};
    int font_weight_{0};

    bool is_checked_{false};
    double progress_t_{0.0};
    double value_t_{0.0};
    bool is_indeterminate_{false};
    double phase_offset_{0.0};
    bool dot_{false};
    std::optional<Color> dot_color_{std::nullopt};
};

} // namespace tkblend
