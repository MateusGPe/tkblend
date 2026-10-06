#include "native_decorator.hpp"
#include "style_engine.hpp"
#include "blit/blit_backend.h"

#include <cstring>
#include <algorithm>
#include <sstream>
#include <stdexcept>

namespace tkblend {

NativeDecorator::NativeDecorator(
    uintptr_t interp_addr,
    const std::string& parent_path,
    const std::string& widget_name,
    int width,
    int height
) : surface_(std::make_unique<Surface>(std::max(1, width), std::max(1, height))) {
    if (!interp_addr) {
        throw std::invalid_argument("interp_addr must not be null");
    }
    if (widget_name.empty()) {
        throw std::invalid_argument("widget_name must not be empty");
    }

    Tcl_Interp* interp = reinterpret_cast<Tcl_Interp*>(interp_addr);
    if (TkBlend_InitStubs(interp) != TCL_OK) {
        throw std::runtime_error("Failed to initialize Tcl/Tk stubs in NativeDecorator");
    }

    Tk_Window main_win = Tk_MainWindow(interp);
    if (!main_win) {
        throw std::runtime_error("Tk_MainWindow is null");
    }

    Tk_Window parent_win = Tk_NameToWindow(interp, parent_path.c_str(), main_win);
    if (!parent_win) {
        throw std::runtime_error("Failed to find parent Tk_Window for path: " + parent_path);
    }

    std::string full_path = (parent_path == ".") ? ("." + widget_name) : (parent_path + "." + widget_name);
    tkwin_ = Tk_CreateWindowFromPath(interp, parent_win, full_path.c_str(), nullptr);
    if (!tkwin_) {
        throw std::runtime_error("Failed to create Tk_Window for path: " + full_path);
    }

    interp_ = interp;
    path_ = full_path;

    Tk_SetClass(tkwin_, "BlendDecorator");
    Tk_GeometryRequest(tkwin_, std::max(1, width), std::max(1, height));

    const long mask = ExposureMask | StructureNotifyMask | EnterWindowMask | LeaveWindowMask | FocusChangeMask;
    Tk_CreateEventHandler(tkwin_, mask, WindowEventHandler, this);
}

NativeDecorator::~NativeDecorator() {
    if (redraw_pending_ && interp_) {
        Tcl_CancelIdleCall(DisplayCallback, this);
        redraw_pending_ = false;
    }
    detach_child();

    if (tkwin_ && interp_) {
        const long mask = ExposureMask | StructureNotifyMask | EnterWindowMask | LeaveWindowMask | FocusChangeMask;
        Tk_DeleteEventHandler(tkwin_, mask, WindowEventHandler, this);
        Tk_DestroyWindow(tkwin_);
        tkwin_ = nullptr;
        interp_ = nullptr;
    }
}

void NativeDecorator::on_window_destroyed() {
    if (redraw_pending_ && interp_) {
        Tcl_CancelIdleCall(DisplayCallback, this);
        redraw_pending_ = false;
    }
    detach_child();
    tkwin_ = nullptr;
    interp_ = nullptr;
}

bool NativeDecorator::attach_child(const std::string& child_path) {
    detach_child();

    if (!interp_ || !tkwin_ || child_path.empty()) {
        return false;
    }

    Tk_Window main_win = Tk_MainWindow(interp_);
    if (!main_win) {
        return false;
    }

    Tk_Window child_win = Tk_NameToWindow(interp_, child_path.c_str(), main_win);
    if (!child_win) {
        return false;
    }

    {
        std::lock_guard<std::mutex> lock(mutex_);
        child_tkwin_ = child_win;
        child_path_ = child_path;
        child_focused_ = false;
        child_hovered_ = false;
    }

    const long mask = FocusChangeMask | EnterWindowMask | LeaveWindowMask | StructureNotifyMask;
    Tk_CreateEventHandler(child_tkwin_, mask, ChildEventHandler, this);

    update_child_shape();
    request_redraw();
    return true;
}

void NativeDecorator::detach_child() {
    Tk_Window old_child = nullptr;
    bool was_shaped = false;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        old_child = child_tkwin_;
        was_shaped = child_is_shaped_;
        child_tkwin_ = nullptr;
        child_path_.clear();
        child_focused_ = false;
        child_hovered_ = false;
        manual_focused_ = false;
        manual_hovered_ = false;
        child_is_shaped_ = false;
    }

    if (old_child && interp_) {
        if (was_shaped && Tk_WindowId(old_child) != None) {
            clear_window_shape(static_cast<uint64_t>(Tk_WindowId(old_child)));
        }
        const long mask = FocusChangeMask | EnterWindowMask | LeaveWindowMask | StructureNotifyMask;
        Tk_DeleteEventHandler(old_child, mask, ChildEventHandler, this);
    }
}

void NativeDecorator::set_focused(bool focused) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        manual_focused_ = focused;
    }
    request_redraw();
}

void NativeDecorator::set_hovered(bool hovered) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        manual_hovered_ = hovered;
    }
    request_redraw();
}

void NativeDecorator::set_clip_child(bool clip) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        clip_child_ = clip;
    }
    update_child_shape();
    request_redraw();
}

void NativeDecorator::set_child_rx(std::optional<double> val) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        child_rx_ = val;
    }
    update_child_shape();
    request_redraw();
}

void NativeDecorator::set_child_ry(std::optional<double> val) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        child_ry_ = val;
    }
    update_child_shape();
    request_redraw();
}

void NativeDecorator::update_child_shape() {
    Tk_Window child = nullptr;
    bool clip = false;
    double crx = 0.0;
    double cry = 0.0;

    {
        std::lock_guard<std::mutex> lock(mutex_);
        child = child_tkwin_;
        clip = clip_child_;
        double default_rx = std::max(0.0, rx_ - border_width_);
        double default_ry = std::max(0.0, ry_ - border_width_);
        crx = child_rx_.value_or(default_rx);
        cry = child_ry_.value_or(default_ry);
    }

    if (!child || !interp_) {
        return;
    }

    if (Tk_WindowId(child) == None) {
        Tk_MakeWindowExist(child);
    }

    Drawable d = Tk_WindowId(child);
    if (d == None) {
        return;
    }

    uint64_t win_id = static_cast<uint64_t>(d);
    int w = Tk_Width(child);
    int h = Tk_Height(child);

    if (clip && w > 0 && h > 0 && crx > 0.0 && cry > 0.0) {
        if (apply_round_rect_shape(win_id, w, h, crx, cry)) {
            std::lock_guard<std::mutex> lock(mutex_);
            child_is_shaped_ = true;
        }
    } else {
        bool was_shaped = false;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            was_shaped = child_is_shaped_;
            child_is_shaped_ = false;
        }
        if (was_shaped) {
            clear_window_shape(win_id);
        }
    }
}

void NativeDecorator::set_geometry_request(int width, int height) {
    if (tkwin_) {
        Tk_GeometryRequest(tkwin_, std::max(1, width), std::max(1, height));
    }
}

void NativeDecorator::request_redraw() {
    if (!tkwin_ || !interp_ || redraw_pending_) {
        return;
    }
    redraw_pending_ = true;
    Tcl_DoWhenIdle(DisplayCallback, this);
}

std::tuple<double, double, double, double> NativeDecorator::get_insets() const {
    std::lock_guard<std::mutex> lock(mutex_);
    double pad_left = 0.0;
    double pad_top = 0.0;
    double pad_right = 0.0;
    double pad_bottom = 0.0;

    if (shadow_enabled_ && shadow_color_.a > 0 && shadow_blur_ > 0.0) {
        double blur_reach = shadow_blur_ * 1.5;
        pad_left = std::max(0.0, blur_reach - shadow_offset_x_);
        pad_top = std::max(0.0, blur_reach - shadow_offset_y_);
        pad_right = std::max(0.0, blur_reach + shadow_offset_x_);
        pad_bottom = std::max(0.0, blur_reach + shadow_offset_y_);
    }

    if (focus_ring_width_ > 0.0) {
        double ring_reach = focus_ring_offset_ + focus_ring_width_;
        pad_left = std::max(pad_left, ring_reach);
        pad_top = std::max(pad_top, ring_reach);
        pad_right = std::max(pad_right, ring_reach);
        pad_bottom = std::max(pad_bottom, ring_reach);
    }

    if (border_width_ > 0.0) {
        double bw_reach = border_width_ / 2.0;
        pad_left = std::max(pad_left, bw_reach);
        pad_top = std::max(pad_top, bw_reach);
        pad_right = std::max(pad_right, bw_reach);
        pad_bottom = std::max(pad_bottom, bw_reach);
    }

    return {pad_left, pad_top, pad_right, pad_bottom};
}

void NativeDecorator::set_style(
    std::optional<Color> bg_color,
    std::optional<Color> hover_bg_color,
    std::optional<Color> focus_bg_color,
    std::optional<Color> parent_bg,
    std::optional<Color> border_color,
    std::optional<Color> border_hover_color,
    std::optional<Color> border_focus_color,
    std::optional<double> border_width,
    std::optional<double> rx,
    std::optional<double> ry,
    std::optional<Color> shadow_color,
    std::optional<double> shadow_blur,
    std::optional<double> shadow_spread,
    std::optional<double> shadow_offset_x,
    std::optional<double> shadow_offset_y,
    std::optional<bool> shadow_enabled,
    std::optional<Color> focus_ring_color,
    std::optional<double> focus_ring_width,
    std::optional<double> focus_ring_offset,
    std::optional<bool> clip_child,
    std::optional<double> child_rx,
    std::optional<double> child_ry
) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (bg_color.has_value()) bg_color_ = *bg_color;
        if (hover_bg_color.has_value()) hover_bg_color_ = hover_bg_color;
        if (focus_bg_color.has_value()) focus_bg_color_ = focus_bg_color;
        if (parent_bg.has_value()) parent_bg_ = *parent_bg;
        if (border_color.has_value()) border_color_ = *border_color;
        if (border_hover_color.has_value()) border_hover_color_ = border_hover_color;
        if (border_focus_color.has_value()) border_focus_color_ = border_focus_color;
        if (border_width.has_value()) border_width_ = *border_width;
        if (rx.has_value()) rx_ = *rx;
        if (ry.has_value()) ry_ = *ry;
        if (shadow_color.has_value()) shadow_color_ = *shadow_color;
        if (shadow_blur.has_value()) shadow_blur_ = *shadow_blur;
        if (shadow_spread.has_value()) shadow_spread_ = *shadow_spread;
        if (shadow_offset_x.has_value()) shadow_offset_x_ = *shadow_offset_x;
        if (shadow_offset_y.has_value()) shadow_offset_y_ = *shadow_offset_y;
        if (shadow_enabled.has_value()) shadow_enabled_ = *shadow_enabled;
        if (focus_ring_color.has_value()) focus_ring_color_ = *focus_ring_color;
        if (focus_ring_width.has_value()) focus_ring_width_ = *focus_ring_width;
        if (focus_ring_offset.has_value()) focus_ring_offset_ = *focus_ring_offset;
        if (clip_child.has_value()) clip_child_ = *clip_child;
        if (child_rx.has_value()) child_rx_ = child_rx;
        if (child_ry.has_value()) child_ry_ = child_ry;
    }

    update_child_shape();
    request_redraw();
}

void NativeDecorator::WindowEventHandler(ClientData clientData, XEvent* eventPtr) {
    auto* self = static_cast<NativeDecorator*>(clientData);
    if (self) {
        self->on_window_event(eventPtr);
    }
}

void NativeDecorator::ChildEventHandler(ClientData clientData, XEvent* eventPtr) {
    auto* self = static_cast<NativeDecorator*>(clientData);
    if (self) {
        self->on_child_event(eventPtr);
    }
}

void NativeDecorator::DisplayCallback(ClientData clientData) {
    auto* self = static_cast<NativeDecorator*>(clientData);
    if (self) {
        self->redraw_pending_ = false;
        self->render_and_present();
    }
}

void NativeDecorator::on_window_event(XEvent* eventPtr) {
    if (!eventPtr || !tkwin_) return;

    switch (eventPtr->type) {
        case Expose: {
            if (eventPtr->xexpose.count == 0) {
                request_redraw();
            }
            break;
        }

        case ConfigureNotify:
        case MapNotify: {
            request_redraw();
            break;
        }

        case DestroyNotify: {
            on_window_destroyed();
            break;
        }

        case EnterNotify: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                dec_hovered_ = true;
            }
            request_redraw();
            break;
        }

        case LeaveNotify: {
            if (eventPtr->xcrossing.detail != NotifyInferior) {
                std::lock_guard<std::mutex> lock(mutex_);
                dec_hovered_ = false;
            }
            request_redraw();
            break;
        }

        case FocusIn: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                dec_focused_ = true;
            }
            request_redraw();
            break;
        }

        case FocusOut: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                dec_focused_ = false;
            }
            request_redraw();
            break;
        }

        default:
            break;
    }
}

void NativeDecorator::on_child_event(XEvent* eventPtr) {
    if (!eventPtr) return;

    switch (eventPtr->type) {
        case FocusIn: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                child_focused_ = true;
            }
            request_redraw();
            break;
        }

        case FocusOut: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                child_focused_ = false;
            }
            request_redraw();
            break;
        }

        case EnterNotify: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                child_hovered_ = true;
            }
            request_redraw();
            break;
        }

        case LeaveNotify: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                child_hovered_ = false;
            }
            request_redraw();
            break;
        }

        case MapNotify:
        case ConfigureNotify: {
            update_child_shape();
            request_redraw();
            break;
        }

        case DestroyNotify: {
            {
                std::lock_guard<std::mutex> lock(mutex_);
                child_tkwin_ = nullptr;
                child_path_.clear();
                child_focused_ = false;
                child_hovered_ = false;
                child_is_shaped_ = false;
            }
            request_redraw();
            break;
        }

        default:
            break;
    }
}

void NativeDecorator::add_class(const std::string& name) {
    if (name.empty()) return;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (std::find(classes_.begin(), classes_.end(), name) == classes_.end()) {
            classes_.push_back(name);
        }
    }
    request_redraw();
}

void NativeDecorator::remove_class(const std::string& name) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = std::find(classes_.begin(), classes_.end(), name);
        if (it != classes_.end()) {
            classes_.erase(it);
        }
    }
    request_redraw();
}

void NativeDecorator::toggle_class(const std::string& name) {
    if (name.empty()) return;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = std::find(classes_.begin(), classes_.end(), name);
        if (it != classes_.end()) {
            classes_.erase(it);
        } else {
            classes_.push_back(name);
        }
    }
    request_redraw();
}

bool NativeDecorator::has_class(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return std::find(classes_.begin(), classes_.end(), name) != classes_.end();
}

std::vector<std::string> NativeDecorator::get_classes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return classes_;
}

void NativeDecorator::set_classes(const std::vector<std::string>& classes) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        classes_ = classes;
    }
    request_redraw();
}

std::string NativeDecorator::class_name() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string res;
    for (size_t i = 0; i < classes_.size(); ++i) {
        if (i > 0) res += " ";
        res += classes_[i];
    }
    return res;
}

void NativeDecorator::set_class_name(const std::string& cls) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        classes_.clear();
        std::stringstream ss(cls);
        std::string token;
        while (ss >> token) {
            classes_.push_back(token);
        }
    }
    request_redraw();
}

void NativeDecorator::set_var(const std::string& key, const std::string& val) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        local_vars_[key] = val;
    }
    request_redraw();
}

std::string NativeDecorator::get_var(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = local_vars_.find(key);
    if (it != local_vars_.end()) return it->second;
    return StyleEngine::instance().get_variable(key);
}

void NativeDecorator::remove_var(const std::string& key) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        local_vars_.erase(key);
    }
    request_redraw();
}

void NativeDecorator::clear_vars() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        local_vars_.clear();
    }
    request_redraw();
}

std::unordered_map<std::string, std::string> NativeDecorator::get_vars() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return local_vars_;
}

void NativeDecorator::bind_batch(const DrawBatch& batch) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        draw_batch_ = std::make_shared<DrawBatch>(batch);
    }
    request_redraw();
}

void NativeDecorator::clear_batch() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        draw_batch_ = nullptr;
    }
    request_redraw();
}

bool NativeDecorator::has_batch() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return draw_batch_ != nullptr;
}

void NativeDecorator::render_and_present() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!tkwin_ || !interp_) return;

    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable d = Tk_WindowId(tkwin_);
    if (d == None) return;

    if (!Tk_IsMapped(tkwin_)) return;

    int w = Tk_Width(tkwin_);
    int h = Tk_Height(tkwin_);
    if (w <= 0 || h <= 0) return;

    if (surface_->width() != w || surface_->height() != h) {
        surface_->resize(w, h);
    }

    bool focused = manual_focused_ || dec_focused_ || child_focused_;
    bool hovered = manual_hovered_ || dec_hovered_ || child_hovered_;

    // Check if C++ DrawBatch is attached
    if (draw_batch_) {
        surface_->clear(parent_bg_);
        uint16_t pseudo = 0;
        if (focused) pseudo |= PseudoState::Focused;
        if (hovered) pseudo |= PseudoState::Hover;
        std::string cls_str;
        for (size_t i = 0; i < classes_.size(); ++i) {
            if (i > 0) cls_str += " ";
            cls_str += classes_[i];
        }
        surface_->execute_batch(*draw_batch_, local_vars_, pseudo, cls_str);
        surface_->flush();

        Ttk_Box box{0, 0, w, h};
        uint8_t* pixels = surface_->data_ptr();
        size_t stride = surface_->stride();
        NativeBlit(tkwin_, d, box, pixels, stride, w, h);
        return;
    }

    // Default Card Vector Rendering
    surface_->clear(parent_bg_);

    double pad_left = 0.0;
    double pad_top = 0.0;
    double pad_right = 0.0;
    double pad_bottom = 0.0;

    if (shadow_enabled_ && shadow_color_.a > 0 && shadow_blur_ > 0.0) {
        double blur_reach = shadow_blur_ * 1.5;
        pad_left = std::max(0.0, blur_reach - shadow_offset_x_);
        pad_top = std::max(0.0, blur_reach - shadow_offset_y_);
        pad_right = std::max(0.0, blur_reach + shadow_offset_x_);
        pad_bottom = std::max(0.0, blur_reach + shadow_offset_y_);
    }

    if (focus_ring_width_ > 0.0) {
        double ring_reach = focus_ring_offset_ + focus_ring_width_;
        pad_left = std::max(pad_left, ring_reach);
        pad_top = std::max(pad_top, ring_reach);
        pad_right = std::max(pad_right, ring_reach);
        pad_bottom = std::max(pad_bottom, ring_reach);
    }

    if (border_width_ > 0.0) {
        double bw_reach = border_width_ / 2.0;
        pad_left = std::max(pad_left, bw_reach);
        pad_top = std::max(pad_top, bw_reach);
        pad_right = std::max(pad_right, bw_reach);
        pad_bottom = std::max(pad_bottom, bw_reach);
    }

    double card_x = pad_left;
    double card_y = pad_top;
    double card_w = std::max(1.0, (double)w - (pad_left + pad_right));
    double card_h = std::max(1.0, (double)h - (pad_top + pad_bottom));

    // Render Drop Shadow
    if (shadow_enabled_ && shadow_color_.a > 0 && shadow_blur_ > 0.0) {
        surface_->draw_shadow_rounded_rect(
            card_x, card_y, card_w, card_h,
            rx_, ry_,
            shadow_blur_, shadow_spread_,
            shadow_offset_x_, shadow_offset_y_,
            shadow_color_
        );
    }

    // Resolve state colors with class resolution fallback
    Color current_bg = bg_color_;
    if (focused && focus_bg_color_.has_value()) {
        current_bg = *focus_bg_color_;
    } else if (hovered && hover_bg_color_.has_value()) {
        current_bg = *hover_bg_color_;
    }

    Color current_border = border_color_;
    if (focused && border_focus_color_.has_value()) {
        current_border = *border_focus_color_;
    } else if (hovered && border_hover_color_.has_value()) {
        current_border = *border_hover_color_;
    }

    // Fill card background
    surface_->fill_rounded_rect(card_x, card_y, card_w, card_h, rx_, ry_, current_bg);

    // Stroke card border
    if (border_width_ > 0.0 && current_border.a > 0) {
        surface_->stroke_rounded_rect(card_x, card_y, card_w, card_h, rx_, ry_, current_border, border_width_);
    }

    // Stroke active focus ring
    if (focused && focus_ring_width_ > 0.0 && focus_ring_color_.a > 0) {
        double ring_offset = focus_ring_offset_;
        double ring_x = card_x - ring_offset;
        double ring_y = card_y - ring_offset;
        double ring_w = card_w + 2.0 * ring_offset;
        double ring_h = card_h + 2.0 * ring_offset;
        double ring_rx = std::max(0.0, rx_ + ring_offset);
        double ring_ry = std::max(0.0, ry_ + ring_offset);
        surface_->stroke_rounded_rect(ring_x, ring_y, ring_w, ring_h, ring_rx, ring_ry, focus_ring_color_, focus_ring_width_);
    }

    surface_->flush();

    // Cross-platform blit to native Tk drawable
    Ttk_Box box{0, 0, w, h};
    uint8_t* pixels = surface_->data_ptr();
    size_t stride = surface_->stride();
    NativeBlit(tkwin_, d, box, pixels, stride, w, h);
}

} // namespace tkblend
