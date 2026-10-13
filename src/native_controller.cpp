#include "native_controller.hpp"
#include "style_engine.hpp"
#include "draw_engine.hpp"
#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <iostream>

namespace tkblend {

NativeWidgetController::NativeWidgetController()
    : internal_surface_(std::make_unique<Surface>(1, 1)) {}

NativeWidgetController::~NativeWidgetController() {
    detach();
    if (on_paint_.is_valid() || on_state_changed_.is_valid() || on_click_.is_valid() || on_resize_.is_valid() || on_change_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_paint_.reset();
        on_state_changed_.reset();
        on_click_.reset();
        on_resize_.reset();
        on_change_.reset();
    }
}

bool NativeWidgetController::attach(uintptr_t interp_addr, const std::string& widget_path) {
    detach();

    if (!interp_addr || widget_path.empty()) {
        return false;
    }

    Tcl_Interp* interp = reinterpret_cast<Tcl_Interp*>(interp_addr);
    if (TkBlend_InitStubs(interp) != TCL_OK) {
        return false;
    }

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
                      FocusChangeMask | ButtonPressMask | ButtonReleaseMask |
                      PointerMotionMask | KeyPressMask | KeyReleaseMask;
    Tk_CreateEventHandler(tkwin_, mask, HandleTkEvent, this);

    request_redraw();
    return true;
}

void NativeWidgetController::detach() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (idle_scheduled_ && interp_) {
        Tcl_CancelIdleCall(IdleRedraw, this);
        idle_scheduled_ = false;
    }
    if (anim_timer_ && interp_) {
        Tcl_DeleteTimerHandler(anim_timer_);
        anim_timer_ = nullptr;
    }

    if (tkwin_ && interp_) {
        const long mask = ExposureMask | StructureNotifyMask | VisibilityChangeMask |
                          EnterWindowMask | LeaveWindowMask |
                          FocusChangeMask | ButtonPressMask | ButtonReleaseMask |
                          PointerMotionMask | KeyPressMask | KeyReleaseMask;
        Tk_DeleteEventHandler(tkwin_, mask, HandleTkEvent, this);
        StyleEngine::instance().unregister_container_window(reinterpret_cast<uintptr_t>(tkwin_));
        if (Tk_WindowId(tkwin_) != None) {
            StyleEngine::instance().unregister_container_window(static_cast<uintptr_t>(Tk_WindowId(tkwin_)));
        }
    }

    tkwin_ = nullptr;
    interp_ = nullptr;
    widget_path_.clear();
    bound_surface_id_ = 0;
    external_surface_ = nullptr;
}

void NativeWidgetController::on_window_destroyed() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (idle_scheduled_ && interp_) {
        Tcl_CancelIdleCall(IdleRedraw, this);
        idle_scheduled_ = false;
    }
    if (anim_timer_ && interp_) {
        Tcl_DeleteTimerHandler(anim_timer_);
        anim_timer_ = nullptr;
    }
    if (tkwin_) {
        StyleEngine::instance().unregister_container_window(reinterpret_cast<uintptr_t>(tkwin_));
        if (Tk_WindowId(tkwin_) != None) {
            StyleEngine::instance().unregister_container_window(static_cast<uintptr_t>(Tk_WindowId(tkwin_)));
        }
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
        if (w > 1) return w;
        int req_w = Tk_ReqWidth(tkwin_);
        if (req_w > 1) return req_w;
        if (w > 0) return w;
    }
    return internal_surface_->width();
}

int NativeWidgetController::height() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (tkwin_) {
        int h = Tk_Height(tkwin_);
        if (h > 1) return h;
        int req_h = Tk_ReqHeight(tkwin_);
        if (req_h > 1) return req_h;
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
    if (win_w <= 0 || win_h <= 0) return;

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

            target_hover_ = is_hovered() ? 1.0f : 0.0f;
            target_press_ = is_pressed() ? 1.0f : 0.0f;
            target_focus_ = is_focused() ? 1.0f : 0.0f;

            if (!animated_) {
                hover_t_ = target_hover_;
                press_t_ = target_press_;
                focus_t_ = target_focus_;
            }
        }
    }
    if (changed) {
        if (animated_) {
            schedule_anim_step();
        }
        if (on_state_changed_.is_valid()) {
            nb::gil_scoped_acquire gil;
            // Copy so the callback may safely replace/clear itself while running.
            nb::object cb = on_state_changed_;
            if (cb.is_valid() && !cb.is_none()) {
                try {
                    cb(s, old_state);
                } catch (const nb::python_error&) {
                    PyErr_Print();
                } catch (...) {}
            }
        }
        request_redraw();
    }
}

void NativeWidgetController::modify_state(uint16_t mask, bool on) {
    uint16_t s;
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        s = state_;
    }
    if (on) s |= mask;
    else s &= static_cast<uint16_t>(~mask);
    set_state(s);
}

void NativeWidgetController::set_hovered(bool hovered) { modify_state(StateHover, hovered); }
void NativeWidgetController::set_pressed(bool pressed) { modify_state(StateActive, pressed); }
void NativeWidgetController::set_focused(bool focused) { modify_state(StateFocused, focused); }
void NativeWidgetController::set_disabled(bool disabled) { modify_state(StateDisabled, disabled); }
void NativeWidgetController::set_checked(bool checked) { modify_state(StateChecked, checked); }

Color NativeWidgetController::parent_bg() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (has_explicit_parent_bg_) {
        return parent_bg_;
    }
    return resolve_parent_bg();
}

void NativeWidgetController::set_parent_bg(const Color& c) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        parent_bg_ = c;
        has_explicit_parent_bg_ = (c.a > 0 || c.r > 0 || c.g > 0 || c.b > 0);
    }
    request_redraw();
}

void NativeWidgetController::clear_parent_bg() {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        parent_bg_ = Color{0, 0, 0, 0};
        has_explicit_parent_bg_ = false;
    }
    request_redraw();
}

Color NativeWidgetController::resolve_parent_bg() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (has_explicit_parent_bg_) {
        return parent_bg_;
    }
    if (!tkwin_) {
        return StyleEngine::instance().get_layer_color(ContainerLayer::Base);
    }
    Tk_Window curr = Tk_Parent(tkwin_);
    while (curr != nullptr) {
        ContainerLayer layer = StyleEngine::instance().resolve_window_layer(reinterpret_cast<uintptr_t>(curr));
        if (layer == ContainerLayer::Base && Tk_WindowId(curr) != None) {
            layer = StyleEngine::instance().resolve_window_layer(static_cast<uintptr_t>(Tk_WindowId(curr)));
        }
        if (layer != ContainerLayer::Base) {
            return StyleEngine::instance().get_layer_color(layer);
        }
        curr = Tk_Parent(curr);
    }
    return StyleEngine::instance().get_layer_color(ContainerLayer::Base);
}

void NativeWidgetController::set_hover_t(float val) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        hover_t_ = std::clamp(val, 0.0f, 1.0f);
        target_hover_ = hover_t_;
    }
    request_redraw();
}

void NativeWidgetController::set_press_t(float val) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        press_t_ = std::clamp(val, 0.0f, 1.0f);
        target_press_ = press_t_;
    }
    request_redraw();
}

void NativeWidgetController::set_focus_t(float val) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        focus_t_ = std::clamp(val, 0.0f, 1.0f);
        target_focus_ = focus_t_;
    }
    request_redraw();
}

void NativeWidgetController::schedule_anim_step() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (!animated_ || anim_timer_ != nullptr || !interp_) return;
    anim_timer_ = Tcl_CreateTimerHandler(16, AnimTimerCallback, this);
}

void NativeWidgetController::AnimTimerCallback(ClientData clientData) {
    auto* ctrl = reinterpret_cast<NativeWidgetController*>(clientData);
    if (ctrl) {
        ctrl->on_anim_tick();
    }
}

void NativeWidgetController::on_anim_tick() {
    bool still_animating = false;
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        anim_timer_ = nullptr;
        // Hover lerp
        float diff_h = target_hover_ - hover_t_;
        if (std::abs(diff_h) > 0.01f) {
            hover_t_ += diff_h * 0.25f;
            still_animating = true;
        } else {
            hover_t_ = target_hover_;
        }

        // Press lerp
        float diff_p = target_press_ - press_t_;
        if (std::abs(diff_p) > 0.01f) {
            press_t_ += diff_p * 0.35f;
            still_animating = true;
        } else {
            press_t_ = target_press_;
        }

        // Focus lerp
        float diff_f = target_focus_ - focus_t_;
        if (std::abs(diff_f) > 0.01f) {
            focus_t_ += diff_f * 0.25f;
            still_animating = true;
        } else {
            focus_t_ = target_focus_;
        }
    }

    request_redraw();

    if (still_animating) {
        schedule_anim_step();
    }
}


void NativeWidgetController::request_redraw() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
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
        {
            std::lock_guard<std::recursive_mutex> lock(self->mutex_);
            self->idle_scheduled_ = false;
        }
        self->paint_and_blit();
    }
}

static KeySym lookup_keysym(XKeyEvent* xkey) {
    KeySym sym = NoSymbol;
#if defined(_WIN32)
    switch (xkey->keycode) {
        case 0x09: /* VK_TAB */    sym = 0xFF09; break;
        case 0x0D: /* VK_RETURN */ sym = 0xFF0D; break;
        case 0x20: /* VK_SPACE */  sym = 0x20;   break;
        default:                   sym = static_cast<KeySym>(xkey->keycode); break;
    }
#elif defined(__APPLE__)
    switch (xkey->keycode) {
        case 48: /* Tab */      sym = 0xFF09; break;
        case 36: /* Return */   sym = 0xFF0D; break;
        case 76: /* KP_Enter */ sym = 0xFF8D; break;
        case 49: /* Space */    sym = 0x20;   break;
        default:                sym = static_cast<KeySym>(xkey->keycode); break;
    }
#else
    char kbuf[32];
    XLookupString(xkey, kbuf, sizeof(kbuf), &sym, nullptr);
#endif
    return sym;
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
            if (auto_focus_ && interp_ && !widget_path_.empty()) {
                std::string cmd = "catch {focus " + widget_path_ + "}";
                TkBlend_Eval(interp_, cmd.c_str());
            }

            if (eventPtr->xbutton.button == 1) {
                if (auto_press_) {
                    set_pressed(true);
                }
                if (widget_class_ == "slider") {
                    int w = width();
                    double track_w = w - 24.0;
                    double pos = (track_w > 0) ? std::clamp((static_cast<double>(eventPtr->xbutton.x) - 12.0) / track_w, 0.0, 1.0) : 0.0;
                    set_var("--thumb-pos", std::to_string(pos));
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(pos)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "range_slider") {
                    int w = width();
                    double track_w = w - 28.0;
                    double pos = (track_w > 0) ? std::clamp((static_cast<double>(eventPtr->xbutton.x) - 14.0) / track_w, 0.0, 1.0) : 0.0;
                    double min_p = 0.25, max_p = 0.75;
                    auto it_min = local_vars_.find("--thumb-min-pos");
                    if (it_min != local_vars_.end()) { try { min_p = std::stod(it_min->second); } catch (...) {} }
                    auto it_max = local_vars_.find("--thumb-max-pos");
                    if (it_max != local_vars_.end()) { try { max_p = std::stod(it_max->second); } catch (...) {} }
                    if (std::abs(pos - min_p) <= std::abs(pos - max_p)) {
                        active_thumb_ = 0;
                        min_p = std::min(pos, max_p);
                        set_var("--thumb-min-pos", std::to_string(min_p));
                    } else {
                        active_thumb_ = 1;
                        max_p = std::max(pos, min_p);
                        set_var("--thumb-max-pos", std::to_string(max_p));
                    }
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::make_tuple(min_p, max_p)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "segmented_button") {
                    int w = width();
                    int count = 2;
                    auto it_c = local_vars_.find("--count");
                    if (it_c != local_vars_.end()) {
                        try { count = std::max(1, std::stoi(it_c->second)); } catch (...) {}
                    }
                    int idx = std::clamp(static_cast<int>(eventPtr->xbutton.x * count / (w > 0 ? w : 1)), 0, count - 1);
                    set_var("--selected-index", std::to_string(idx));
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(idx)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "scrollbar") {
                    bool is_horiz = false;
                    auto it_ori = local_vars_.find("--orientation");
                    if (it_ori != local_vars_.end() && it_ori->second == "horizontal") {
                        is_horiz = true;
                    } else if (width() > height() * 1.5) {
                        is_horiz = true;
                    }
                    int total_len = is_horiz ? width() : height();
                    double mouse_coord = is_horiz ? static_cast<double>(eventPtr->xbutton.x) : static_cast<double>(eventPtr->xbutton.y);
                    double thumb_sz = 0.3;
                    auto it_sz = local_vars_.find("--thumb-size");
                    if (it_sz != local_vars_.end()) { try { thumb_sz = std::clamp(std::stod(it_sz->second), 0.05, 1.0); } catch (...) {} }
                    double min_sz = std::min(static_cast<double>(total_len), 28.0);
                    double max_sz = std::max(min_sz, total_len * 0.30);
                    double thumb_len = std::clamp(total_len * thumb_sz, min_sz, max_sz);
                    double available_len = std::max(1.0, total_len - thumb_len);
                    double progress = std::clamp((mouse_coord - thumb_len / 2.0) / available_len, 0.0, 1.0);
                    set_var("--thumb-pos", std::to_string(progress));
                    set_var("--thumb-progress", std::to_string(progress));
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(progress)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "switch" || widget_class_ == "checkbox") {
                    set_checked(!is_checked());
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(is_checked())); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "radio") {
                    set_checked(true);
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(true)); } catch (...) {}
                    }
                    request_redraw();
                }
            }
            break;
        }

        case MotionNotify: {
            if (eventPtr->xmotion.state & Button1Mask) {
                if (widget_class_ == "slider") {
                    int w = width();
                    double track_w = w - 24.0;
                    double pos = (track_w > 0) ? std::clamp((static_cast<double>(eventPtr->xmotion.x) - 12.0) / track_w, 0.0, 1.0) : 0.0;
                    set_var("--thumb-pos", std::to_string(pos));
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(pos)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "range_slider") {
                    int w = width();
                    double track_w = w - 28.0;
                    double pos = (track_w > 0) ? std::clamp((static_cast<double>(eventPtr->xmotion.x) - 14.0) / track_w, 0.0, 1.0) : 0.0;
                    double min_p = 0.25, max_p = 0.75;
                    auto it_min = local_vars_.find("--thumb-min-pos");
                    if (it_min != local_vars_.end()) { try { min_p = std::stod(it_min->second); } catch (...) {} }
                    auto it_max = local_vars_.find("--thumb-max-pos");
                    if (it_max != local_vars_.end()) { try { max_p = std::stod(it_max->second); } catch (...) {} }
                    if (active_thumb_ == 0) {
                        min_p = std::min(pos, max_p);
                        set_var("--thumb-min-pos", std::to_string(min_p));
                    } else {
                        max_p = std::max(pos, min_p);
                        set_var("--thumb-max-pos", std::to_string(max_p));
                    }
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::make_tuple(min_p, max_p)); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "scrollbar") {
                    bool is_horiz = false;
                    auto it_ori = local_vars_.find("--orientation");
                    if (it_ori != local_vars_.end() && it_ori->second == "horizontal") {
                        is_horiz = true;
                    } else if (width() > height() * 1.5) {
                        is_horiz = true;
                    }
                    int total_len = is_horiz ? width() : height();
                    double mouse_coord = is_horiz ? static_cast<double>(eventPtr->xmotion.x) : static_cast<double>(eventPtr->xmotion.y);
                    double thumb_sz = 0.3;
                    auto it_sz = local_vars_.find("--thumb-size");
                    if (it_sz != local_vars_.end()) { try { thumb_sz = std::clamp(std::stod(it_sz->second), 0.05, 1.0); } catch (...) {} }
                    double min_sz = std::min(static_cast<double>(total_len), 28.0);
                    double max_sz = std::max(min_sz, total_len * 0.30);
                    double thumb_len = std::clamp(total_len * thumb_sz, min_sz, max_sz);
                    double available_len = std::max(1.0, total_len - thumb_len);
                    double progress = std::clamp((mouse_coord - thumb_len / 2.0) / available_len, 0.0, 1.0);
                    set_var("--thumb-pos", std::to_string(progress));
                    set_var("--thumb-progress", std::to_string(progress));
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(progress)); } catch (...) {}
                    }
                    request_redraw();
                }
            }
            break;
        }

        case ButtonRelease: {
            const unsigned int button = eventPtr->xbutton.button;
            const bool primary = (button == 1);
            const bool was_pressed = is_pressed();
            if (auto_press_ && primary) {
                set_pressed(false);
            }
            const bool fire = !auto_press_ || !primary || was_pressed;
            if (fire && on_click_.is_valid()) {
                nb::gil_scoped_acquire gil;
                nb::object cb = on_click_;
                if (cb.is_valid() && !cb.is_none()) {
                    try {
                        cb(eventPtr->xbutton.x, eventPtr->xbutton.y, button);
                    } catch (const nb::python_error&) {
                        PyErr_Print();
                    } catch (...) {}
                }
            }
            break;
        }

        case KeyPress: {
            KeySym sym = lookup_keysym(&eventPtr->xkey);
            if (sym == 0xFF09 || sym == 0x09 /* Tab */) {
                if (interp_ && !widget_path_.empty()) {
                    bool shift = (eventPtr->xkey.state & ShiftMask) != 0;
                    std::string cmd = shift ? ("catch {tk::TabToWindow [tk_focusPrev " + widget_path_ + "]}")
                                            : ("catch {tk::TabToWindow [tk_focusNext " + widget_path_ + "]}");
                    TkBlend_Eval(interp_, cmd.c_str());
                }
            } else if (sym == 0x20 /* Space */ || sym == 0xFF0D || sym == 0x0D /* Return */ || sym == 0xFF8D /* KP_Enter */) {
                if (widget_class_ == "button") {
                    set_pressed(true);
                    if (on_click_.is_valid() && !on_click_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_click_(width() / 2, height() / 2, 1); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "switch" || widget_class_ == "checkbox") {
                    set_checked(!is_checked());
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(is_checked())); } catch (...) {}
                    }
                    request_redraw();
                } else if (widget_class_ == "radio") {
                    set_checked(true);
                    if (on_change_.is_valid() && !on_change_.is_none()) {
                        nb::gil_scoped_acquire gil;
                        try { on_change_(nb::cast(true)); } catch (...) {}
                    }
                    request_redraw();
                }
            }
            break;
        }

        case KeyRelease: {
            KeySym sym = lookup_keysym(&eventPtr->xkey);
            if ((sym == 0x20 || sym == 0xFF0D || sym == 0x0D || sym == 0xFF8D) && widget_class_ == "button") {
                set_pressed(false);
                request_redraw();
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

    std::unordered_map<std::string, std::string> vars_copy;
    std::string cls_str;
    uint16_t current_state = 0;
    std::shared_ptr<DrawBatch> local_batch;
    std::vector<std::string> classes_copy;

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

        local_vars_["--hover-t"] = std::to_string(hover_t_);
        local_vars_["--press-t"] = std::to_string(press_t_);
        local_vars_["--focus-t"] = std::to_string(focus_t_);
        if (win_w > 0 && win_h > 0) {
            local_vars_["--width"] = std::to_string(win_w);
            local_vars_["--height"] = std::to_string(win_h);
            local_vars_["--w"] = std::to_string(win_w);
            local_vars_["--h"] = std::to_string(win_h);
            local_vars_["--w_fr"] = std::to_string(win_w + 4);
            local_vars_["--h_fr"] = std::to_string(win_h + 4);
            local_vars_["--text-x"] = std::to_string(win_w / 2.0);
            float press_off = (press_t_ > 0.0f) ? (1.0f * press_t_) : 0.0f;
            local_vars_["--text-y"] = std::to_string(win_h / 2.0 + 13.0 * 0.35 + press_off);
        }
        if (local_vars_.find("--focus-ring-width") == local_vars_.end()) {
            local_vars_["--focus-ring-width"] = std::to_string(2.0f * focus_t_);
        }
        if (local_vars_.find("--thumb-pos") != local_vars_.end() && win_w > 0) {
            try {
                double t = std::clamp(std::stod(local_vars_["--thumb-pos"]), 0.0, 1.0);
                double track_w = std::max(0.0, win_w - 24.0);
                local_vars_["--active-w"] = std::to_string(track_w * t);
                local_vars_["--thumb-x"] = std::to_string(12.0 + track_w * t);
                local_vars_["--thumb-y"] = std::to_string(win_h / 2.0);
            } catch (...) {}
        }
        if (local_vars_.find("--progress") != local_vars_.end() && win_w > 0) {
            try {
                double p = std::clamp(std::stod(local_vars_["--progress"]), 0.0, 1.0);
                local_vars_["--progress-w"] = std::to_string(win_w * p);
            } catch (...) {}
        }
        vars_copy = local_vars_;

        for (size_t i = 0; i < classes_.size(); ++i) {
            if (i > 0) cls_str += " ";
            cls_str += classes_[i];
        }
        classes_copy = classes_;
        current_state = state_;
        local_batch = draw_batch_;
    }

    if (!surf || surf->width() <= 0 || surf->height() <= 0) {
        return;
    }

    Color eff_parent_bg = resolve_parent_bg();
    vars_copy["--parent-bg"] = eff_parent_bg.to_hex();

    DrawBatch dynamically_created_batch;
    const DrawBatch* batch_to_run = local_batch.get();
    if (!batch_to_run && !widget_class_.empty()) {
        dynamically_created_batch = DrawEngine::instance().create_control_batch(widget_class_, current_state, win_w, win_h, vars_copy);
        if (dynamically_created_batch.size() > 0) {
            batch_to_run = &dynamically_created_batch;
        } else {
            batch_to_run = DrawEngine::instance().get_batch(widget_class_, current_state);
        }
    }
    if (!batch_to_run) {
        for (const auto& c : classes_copy) {
            dynamically_created_batch = DrawEngine::instance().create_control_batch(c, current_state, win_w, win_h, vars_copy);
            if (dynamically_created_batch.size() > 0) {
                batch_to_run = &dynamically_created_batch;
                break;
            }
            batch_to_run = DrawEngine::instance().get_batch(c, current_state);
            if (batch_to_run) break;
            batch_to_run = StyleEngine::instance().get_element_batch(c);
            if (batch_to_run) break;
        }
    }

    if (batch_to_run) {
        surf->clear(eff_parent_bg);
        surf->execute_batch(*batch_to_run, vars_copy, current_state, cls_str);
    } else {
        nb::gil_scoped_acquire gil;
        if (on_paint_.is_valid() && !on_paint_.is_none()) {
            surf->clear(eff_parent_bg);
            try {
                on_paint_(nb::cast(surf, nb::rv_policy::reference));
            } catch (const nb::python_error&) {
                PyErr_Print();
            } catch (...) {}
        }
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
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    on_paint_ = callback;
}

void NativeWidgetController::clear_on_paint() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (on_paint_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_paint_.reset();
    }
}

void NativeWidgetController::set_on_state_changed(nb::object callback) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    on_state_changed_ = callback;
}

void NativeWidgetController::clear_on_state_changed() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (on_state_changed_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_state_changed_.reset();
    }
}

void NativeWidgetController::set_on_click(nb::object callback) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    on_click_ = callback;
}

void NativeWidgetController::clear_on_click() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (on_click_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_click_.reset();
    }
}

void NativeWidgetController::set_on_resize(nb::object callback) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    on_resize_ = callback;
}

void NativeWidgetController::clear_on_resize() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (on_resize_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_resize_.reset();
    }
}

void NativeWidgetController::add_class(const std::string& name) {
    if (name.empty()) return;
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        if (std::find(classes_.begin(), classes_.end(), name) == classes_.end()) {
            classes_.push_back(name);
        }
    }
    request_redraw();
}

void NativeWidgetController::remove_class(const std::string& name) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        auto it = std::find(classes_.begin(), classes_.end(), name);
        if (it != classes_.end()) {
            classes_.erase(it);
        }
    }
    request_redraw();
}

void NativeWidgetController::toggle_class(const std::string& name) {
    if (name.empty()) return;
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        auto it = std::find(classes_.begin(), classes_.end(), name);
        if (it != classes_.end()) {
            classes_.erase(it);
        } else {
            classes_.push_back(name);
        }
    }
    request_redraw();
}

bool NativeWidgetController::has_class(const std::string& name) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    return std::find(classes_.begin(), classes_.end(), name) != classes_.end();
}

std::vector<std::string> NativeWidgetController::get_classes() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    return classes_;
}

void NativeWidgetController::set_classes(const std::vector<std::string>& classes) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        classes_ = classes;
    }
    request_redraw();
}

std::string NativeWidgetController::class_name() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    std::string res;
    for (size_t i = 0; i < classes_.size(); ++i) {
        if (i > 0) res += " ";
        res += classes_[i];
    }
    return res;
}

void NativeWidgetController::set_class_name(const std::string& cls) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        classes_.clear();
        std::stringstream ss(cls);
        std::string token;
        while (ss >> token) {
            classes_.push_back(token);
        }
    }
    request_redraw();
}

void NativeWidgetController::set_var(const std::string& key, const std::string& val) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        local_vars_[key] = val;
    }
    request_redraw();
}

std::string NativeWidgetController::get_var(const std::string& key) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    auto it = local_vars_.find(key);
    if (it != local_vars_.end()) return it->second;
    return StyleEngine::instance().get_variable(key);
}

void NativeWidgetController::remove_var(const std::string& key) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        local_vars_.erase(key);
    }
    request_redraw();
}

void NativeWidgetController::clear_vars() {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        local_vars_.clear();
    }
    request_redraw();
}

std::unordered_map<std::string, std::string> NativeWidgetController::get_vars() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    return local_vars_;
}

void NativeWidgetController::bind_batch(const DrawBatch& batch) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        draw_batch_ = std::make_shared<DrawBatch>(batch);
    }
    request_redraw();
}

void NativeWidgetController::clear_batch() {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        draw_batch_ = nullptr;
    }
    request_redraw();
}

bool NativeWidgetController::has_batch() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    if (draw_batch_ != nullptr) return true;
    if (!widget_class_.empty()) {
        return DrawEngine::instance().has_batch(widget_class_, state_);
    }
    return false;
}

void NativeWidgetController::set_widget_class(const std::string& wc) {
    {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        widget_class_ = wc;
    }
    request_redraw();
}

void NativeWidgetController::set_on_change(nb::object callback) {
    on_change_ = callback;
}

void NativeWidgetController::clear_on_change() {
    if (on_change_.is_valid()) {
        nb::gil_scoped_acquire gil;
        on_change_.reset();
    }
}

} // namespace tkblend
