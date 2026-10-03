#pragma once

#include "platform_compat.h"
#include "surface.hpp"
#include "surface_registry.hpp"
#include "blit/blit_backend.h"
#include "color.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/optional.h>

#include <string>
#include <memory>
#include <mutex>
#include <cstdint>

namespace nb = nanobind;

namespace tkblend {

// Bitmask flags for native widget state
enum ControllerPseudoState : uint16_t {
    StateNormal   = 0,
    StateHover    = 1 << 0,
    StateActive   = 1 << 1, // Pressed
    StateFocused  = 1 << 2,
    StateDisabled = 1 << 3,
    StateChecked  = 1 << 4
};

class NativeWidgetController {
public:
    NativeWidgetController();
    ~NativeWidgetController();

    NativeWidgetController(const NativeWidgetController&) = delete;
    NativeWidgetController& operator=(const NativeWidgetController&) = delete;

    // Attach / Detach native Tk window event handler
    bool attach(uintptr_t interp_addr, const std::string& widget_path);
    void detach();
    bool is_attached() const { return tkwin_ != nullptr; }
    const std::string& widget_path() const { return widget_path_; }

    // Geometry negotiation
    void set_geometry_request(int req_w, int req_h);
    int width() const;
    int height() const;

    // Redraw scheduling & presentation
    void request_redraw();
    void paint_and_blit();

    // Dual-Mode Surface Management
    Surface& surface();
    bool has_bound_surface() const { return bound_surface_id_ != 0 || external_surface_ != nullptr; }
    uint64_t bound_surface_id() const { return bound_surface_id_; }
    void bind_surface(Surface& surf);
    void bind_surface_handle(SurfaceHandle& handle);
    void bind_surface_id(uint64_t id);
    void unbind_surface();

    // Direct blit helpers
    void blit_surface(Surface& surf);
    void blit_handle(SurfaceHandle& handle);

    // State inspection and control
    uint16_t state() const { return state_; }
    void set_state(uint16_t s);

    bool is_hovered() const { return (state_ & StateHover) != 0; }
    void set_hovered(bool hovered);

    bool is_pressed() const { return (state_ & StateActive) != 0; }
    void set_pressed(bool pressed);

    bool is_focused() const { return (state_ & StateFocused) != 0; }
    void set_focused(bool focused);

    bool is_disabled() const { return (state_ & StateDisabled) != 0; }
    void set_disabled(bool disabled);

    bool is_checked() const { return (state_ & StateChecked) != 0; }
    void set_checked(bool checked);

    bool auto_hover() const { return auto_hover_; }
    void set_auto_hover(bool enable) { auto_hover_ = enable; }

    bool auto_press() const { return auto_press_; }
    void set_auto_press(bool enable) { auto_press_ = enable; }

    bool auto_focus() const { return auto_focus_; }
    void set_auto_focus(bool enable) { auto_focus_ = enable; }

    const Color& parent_bg() const { return parent_bg_; }
    void set_parent_bg(const Color& c) { parent_bg_ = c; }

    // GIL-Safe Python Callbacks
    void set_on_paint(nb::object callback);
    void clear_on_paint();

    void set_on_state_changed(nb::object callback);
    void clear_on_state_changed();

    void set_on_click(nb::object callback);
    void clear_on_click();

    void set_on_resize(nb::object callback);
    void clear_on_resize();

private:
    static void HandleTkEvent(ClientData clientData, XEvent* eventPtr);
    static void IdleRedraw(ClientData clientData);

    void on_tk_event(XEvent* eventPtr);
    void on_window_destroyed();
    void blit_active_surface();
    Surface* get_active_surface();

    Tk_Window tkwin_{nullptr};
    Tcl_Interp* interp_{nullptr};
    std::string widget_path_;

    std::unique_ptr<Surface> internal_surface_;
    Surface* external_surface_{nullptr};
    uint64_t bound_surface_id_{0};
    mutable std::recursive_mutex mutex_;

    bool idle_scheduled_{false};
    bool auto_hover_{true};
    bool auto_press_{true};
    bool auto_focus_{true};

    uint16_t state_{StateNormal};
    Color parent_bg_{0, 0, 0, 0};

    nb::object on_paint_;
    nb::object on_state_changed_;
    nb::object on_click_;
    nb::object on_resize_;
};

} // namespace tkblend
