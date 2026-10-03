#include "native_controller.hpp"
#include <algorithm>
#include <stdexcept>
#include <iostream>

namespace tkblend {

NativeWidgetController::NativeWidgetController()
    : internal_surface_(std::make_unique<Surface>(1, 1)) {}

NativeWidgetController::~NativeWidgetController() {
    detach();
    if (on_paint_.is_valid() || on_state_changed_.is_valid() || on_click_.is_valid() || on_resize_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_paint_.reset();
        on_state_changed_.reset();
        on_click_.reset();
        on_resize_.reset();
    }
}

bool NativeWidgetController::attach(uintptr_t interp_addr, const std::string& widget_path) {
    detach();

    if (!interp_addr || widget_path.empty()) {
        return false;
    }

    Tcl_Interp* interp = reinterpret_cast<Tcl_Interp*>(interp_addr);
#if defined(USE_TCL_STUBS) && defined(USE_TK_STUBS)
    if (!Tcl_InitStubs(interp, "8.6", 0) || !Tk_InitStubs(interp, "8.6", 0)) {
        return false;
    }
#endif

    Tk_Window main_win = Tk_MainWindow(interp);
    if (!main_win) {
        return false;
    }

    Tk_Window tkwin = Tk_NameToWindow(interp, widget_path.c_str(), main_win);
    if (!tkwin) {
        return false;
    }

    interp_ = interp;
    tkwin_ = tkwin;
    widget_path_ = widget_path;

    int w = Tk_Width(tkwin_);
    int h = Tk_Height(tkwin_);
    if (w > 0 && h > 0) {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        internal_surface_->resize(w, h);
    }

    const long mask = ExposureMask | StructureNotifyMask | VisibilityChangeMask |
                      EnterWindowMask | LeaveWindowMask |
                      FocusChangeMask | ButtonPressMask | ButtonReleaseMask;
    Tk_CreateEventHandler(tkwin_, mask, HandleTkEvent, this);

    request_redraw();
    return true;
}

void NativeWidgetController::detach() {
    if (idle_scheduled_ && interp_) {
        Tcl_CancelIdleCall(IdleRedraw, this);
        idle_scheduled_ = false;
    }

    if (tkwin_ && interp_) {
        const long mask = ExposureMask | StructureNotifyMask | VisibilityChangeMask |
                          EnterWindowMask | LeaveWindowMask |
                          FocusChangeMask | ButtonPressMask | ButtonReleaseMask;
        Tk_DeleteEventHandler(tkwin_, mask, HandleTkEvent, this);
    }

    tkwin_ = nullptr;
    interp_ = nullptr;
    widget_path_.clear();
    bound_surface_id_ = 0;
    external_surface_ = nullptr;
}

void NativeWidgetController::on_window_destroyed() {
    if (idle_scheduled_ && interp_) {
        Tcl_CancelIdleCall(IdleRedraw, this);
        idle_scheduled_ = false;
    }
    tkwin_ = nullptr;
    interp_ = nullptr;
    widget_path_.clear();
    bound_surface_id_ = 0;
    external_surface_ = nullptr;
}

void NativeWidgetController::set_geometry_request(int req_w, int req_h) {
    if (tkwin_) {
        Tk_GeometryRequest(tkwin_, std::max(1, req_w), std::max(1, req_h));
    }
}

int NativeWidgetController::width() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (tkwin_) {
        int w = Tk_Width(tkwin_);
        if (w > 0) return w;
    }
    return internal_surface_->width();
}

int NativeWidgetController::height() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (tkwin_) {
        int h = Tk_Height(tkwin_);
        if (h > 0) return h;
    }
    return internal_surface_->height();
}

Surface& NativeWidgetController::surface() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    return *internal_surface_;
}

void NativeWidgetController::bind_surface(Surface& surf) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        external_surface_ = &surf;
        bound_surface_id_ = 0;
    }
    request_redraw();
}

void NativeWidgetController::bind_surface_handle(SurfaceHandle& handle) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        external_surface_ = nullptr;
        bound_surface_id_ = handle.surface_id();
    }
    request_redraw();
}

void NativeWidgetController::bind_surface_id(uint64_t id) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        external_surface_ = nullptr;
        bound_surface_id_ = id;
    }
    request_redraw();
}

void NativeWidgetController::unbind_surface() {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        external_surface_ = nullptr;
        bound_surface_id_ = 0;
    }
    request_redraw();
}

void NativeWidgetController::blit_surface(Surface& surf) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (!tkwin_ || !interp_) return;

    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    if (!Tk_IsMapped(tkwin_)) return;

    int win_w = Tk_Width(tkwin_);
    int win_h = Tk_Height(tkwin_);
    if (win_w <= 1 || win_h <= 1) return;

    surf.flush();
    Ttk_Box box{0, 0, win_w, win_h};
    uint8_t* pixels = surf.data_ptr();
    size_t stride = surf.stride();
    NativeBlit(tkwin_, drawable, box, pixels, stride, surf.width(), surf.height());
}

void NativeWidgetController::blit_handle(SurfaceHandle& handle) {
    Surface* s = handle.get();
    if (s) {
        blit_surface(*s);
    }
}

void NativeWidgetController::set_state(uint16_t s) {
    bool changed = false;
    uint16_t old_state = 0;
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        if (state_ != s) {
            old_state = state_;
            state_ = s;
            changed = true;
        }
    }
    if (changed) {
        if (on_state_changed_.is_valid() && !on_state_changed_.is_none()) {
            nb::gil_scoped_acquire gil;
            try {
                on_state_changed_(s, old_state);
            } catch (const nb::python_error&) {
                PyErr_Print();
            } catch (...) {}
        }
        request_redraw();
    }
}

void NativeWidgetController::set_hovered(bool hovered) {
    uint16_t s = state_;
    if (hovered) s |= StateHover;
    else s &= ~StateHover;
    set_state(s);
}

void NativeWidgetController::set_pressed(bool pressed) {
    uint16_t s = state_;
    if (pressed) s |= StateActive;
    else s &= ~StateActive;
    set_state(s);
}

void NativeWidgetController::set_focused(bool focused) {
    uint16_t s = state_;
    if (focused) s |= StateFocused;
    else s &= ~StateFocused;
    set_state(s);
}

void NativeWidgetController::set_disabled(bool disabled) {
    uint16_t s = state_;
    if (disabled) s |= StateDisabled;
    else s &= ~StateDisabled;
    set_state(s);
}

void NativeWidgetController::set_checked(bool checked) {
    uint16_t s = state_;
    if (checked) s |= StateChecked;
    else s &= ~StateChecked;
    set_state(s);
}

void NativeWidgetController::request_redraw() {
    if (!tkwin_ || !interp_ || idle_scheduled_) {
        return;
    }
    idle_scheduled_ = true;
    Tcl_DoWhenIdle(IdleRedraw, this);
}

void NativeWidgetController::HandleTkEvent(ClientData clientData, XEvent* eventPtr) {
    auto* self = static_cast<NativeWidgetController*>(clientData);
    if (self) {
        self->on_tk_event(eventPtr);
    }
}

void NativeWidgetController::IdleRedraw(ClientData clientData) {
    auto* self = static_cast<NativeWidgetController*>(clientData);
    if (self) {
        self->idle_scheduled_ = false;
        self->paint_and_blit();
    }
}

void NativeWidgetController::on_tk_event(XEvent* eventPtr) {
    if (!eventPtr || !tkwin_) return;

    switch (eventPtr->type) {
        case Expose: {
            if (eventPtr->xexpose.count == 0) {
                request_redraw();
            }
            break;
        }

        case ConfigureNotify: {
            int new_w = eventPtr->xconfigure.width;
            int new_h = eventPtr->xconfigure.height;
            {
                std::lock_guard<std::recursive_mutex> lock(mutex_);
                if (new_w > 0 && new_h > 0 &&
                    (internal_surface_->width() != new_w || internal_surface_->height() != new_h)) {
                    internal_surface_->resize(new_w, new_h);
                }
            }
            if (on_resize_.is_valid() && !on_resize_.is_none()) {
                nb::gil_scoped_acquire gil;
                try {
                    on_resize_(new_w, new_h);
                } catch (const nb::python_error&) {
                    PyErr_Print();
                } catch (...) {}
            }
            request_redraw();
            break;
        }

        case MapNotify: {
            request_redraw();
            break;
        }

        case VisibilityNotify: {
            if (eventPtr->xvisibility.state != VisibilityFullyObscured) {
                request_redraw();
            }
            break;
        }

        case DestroyNotify: {
            on_window_destroyed();
            break;
        }

        case EnterNotify: {
            if (auto_hover_) {
                set_hovered(true);
            }
            break;
        }

        case LeaveNotify: {
            if (auto_hover_ && eventPtr->xcrossing.detail != NotifyInferior) {
                set_hovered(false);
                if (auto_press_ && is_pressed()) {
                    set_pressed(false);
                }
            }
            break;
        }

        case FocusIn: {
            if (auto_focus_ && eventPtr->xfocus.detail != NotifyInferior) {
                set_focused(true);
            }
            break;
        }

        case FocusOut: {
            if (auto_focus_ && eventPtr->xfocus.detail != NotifyInferior) {
                set_focused(false);
            }
            break;
        }

        case ButtonPress: {
            if (auto_press_ && eventPtr->xbutton.button == 1) {
                set_pressed(true);
            }
            break;
        }

        case ButtonRelease: {
            bool was_pressed = is_pressed();
            if (auto_press_ && eventPtr->xbutton.button == 1) {
                set_pressed(false);
            }
            if ((was_pressed || !auto_press_) && on_click_.is_valid() && !on_click_.is_none()) {
                nb::gil_scoped_acquire gil;
                try {
                    on_click_(eventPtr->xbutton.x, eventPtr->xbutton.y, eventPtr->xbutton.button);
                } catch (const nb::python_error&) {
                    PyErr_Print();
                } catch (...) {}
            }
            break;
        }

        default:
            break;
    }
}

Surface* NativeWidgetController::get_active_surface() {
    if (external_surface_) {
        return external_surface_;
    }
    if (bound_surface_id_ != 0) {
        auto* s = SurfaceRegistry::instance().get_surface(bound_surface_id_);
        if (s) return s;
    }
    return internal_surface_.get();
}

void NativeWidgetController::paint_and_blit() {
    Surface* surf = nullptr;
    int win_w = 0;
    int win_h = 0;

    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        if (tkwin_) {
            win_w = Tk_Width(tkwin_);
            win_h = Tk_Height(tkwin_);
        }
        surf = get_active_surface();
        if (surf && bound_surface_id_ == 0 && external_surface_ == nullptr) {
            if (win_w > 0 && win_h > 0 && (surf->width() != win_w || surf->height() != win_h)) {
                surf->resize(win_w, win_h);
            }
        }
    }
    if (!surf || surf->width() <= 0 || surf->height() <= 0) {
        return;
    }

    if (on_paint_.is_valid() && !on_paint_.is_none()) {
        nb::gil_scoped_acquire gil;
        try {
            on_paint_(nb::cast(surf, nb::rv_policy::reference));
        } catch (const nb::python_error&) {
            PyErr_Print();
        } catch (...) {}
    }

    blit_active_surface();
}

void NativeWidgetController::blit_active_surface() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (!tkwin_ || !interp_) return;

    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    if (!Tk_IsMapped(tkwin_)) return;

    int win_w = Tk_Width(tkwin_);
    int win_h = Tk_Height(tkwin_);
    if (win_w <= 0 || win_h <= 0) return;

    Surface* surf = get_active_surface();
    if (!surf) return;

    if (bound_surface_id_ == 0 && external_surface_ == nullptr) {
        if (surf->width() != win_w || surf->height() != win_h) {
            return;
        }
    }

    surf->flush();
    Ttk_Box box{0, 0, win_w, win_h};
    uint8_t* pixels = surf->data_ptr();
    size_t stride = surf->stride();
    NativeBlit(tkwin_, drawable, box, pixels, stride, surf->width(), surf->height());
}

void NativeWidgetController::set_on_paint(nb::object callback) {
    on_paint_ = callback;
}

void NativeWidgetController::clear_on_paint() {
    on_paint_.reset();
}

void NativeWidgetController::set_on_state_changed(nb::object callback) {
    on_state_changed_ = callback;
}

void NativeWidgetController::clear_on_state_changed() {
    on_state_changed_.reset();
}

void NativeWidgetController::set_on_click(nb::object callback) {
    on_click_ = callback;
}

void NativeWidgetController::clear_on_click() {
    on_click_.reset();
}

void NativeWidgetController::set_on_resize(nb::object callback) {
    on_resize_ = callback;
}

void NativeWidgetController::clear_on_resize() {
    on_resize_.reset();
}

} // namespace tkblend
