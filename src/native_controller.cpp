#include "native_controller.hpp"
#include <iostream>

namespace tkblend {

NativeWidgetController::NativeWidgetController()
    : surface_(std::make_unique<Surface>(10, 10)) {}

NativeWidgetController::~NativeWidgetController() {
    detach();
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

    // Intercept native Expose, Configure, and Destroy events for instant blitting
    const long mask = ExposureMask | StructureNotifyMask | DestroyNotify;
    Tk_CreateEventHandler(tkwin_, mask, HandleTkEvent, this);

    return true;
}

void NativeWidgetController::detach() {
    if (tkwin_ && interp_) {
        if (idle_scheduled_) {
            Tcl_CancelIdleCall(IdleRedraw, this);
            idle_scheduled_ = false;
        }

        const long mask = ExposureMask | StructureNotifyMask | DestroyNotify;
        Tk_DeleteEventHandler(tkwin_, mask, HandleTkEvent, this);
    }

    tkwin_ = nullptr;
    interp_ = nullptr;
    widget_path_.clear();
}

void NativeWidgetController::set_geometry_request(int req_w, int req_h) {
    if (tkwin_) {
        Tk_GeometryRequest(tkwin_, std::max(1, req_w), std::max(1, req_h));
    }
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
        self->blit_bound_surface();
    }
}

void NativeWidgetController::on_tk_event(XEvent* eventPtr) {
    if (!eventPtr || !tkwin_) return;

    switch (eventPtr->type) {
        case Expose: {
            if (eventPtr->xexpose.count == 0) {
                blit_bound_surface();
            }
            break;
        }

        case ConfigureNotify: {
            break;
        }

        case DestroyNotify: {
            tkwin_ = nullptr;
            interp_ = nullptr;
            idle_scheduled_ = false;
            break;
        }

        default:
            break;
    }
}

void NativeWidgetController::blit_bound_surface() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!tkwin_ || bound_surface_id_ == 0) return;

    auto* surf = SurfaceRegistry::instance().get_surface(bound_surface_id_);
    if (!surf) return;

    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    int win_w = Tk_Width(tkwin_);
    int win_h = Tk_Height(tkwin_);
    if (win_w <= 1 || win_h <= 1) return;

    Ttk_Box box{0, 0, win_w, win_h};
    surf->flush();
    uint8_t* pixels = surf->data_ptr();
    size_t stride = surf->stride();
    NativeBlit(tkwin_, drawable, box, pixels, stride, surf->width(), surf->height());
}

void NativeWidgetController::paint_and_blit() {
    blit_bound_surface();
}

void NativeWidgetController::blit_handle(SurfaceHandle& handle) {
    std::lock_guard<std::mutex> lock(mutex_);
    bound_surface_id_ = handle.surface_id();

    if (!tkwin_) return;
    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    int win_w = Tk_Width(tkwin_);
    int win_h = Tk_Height(tkwin_);
    if (win_w <= 1 || win_h <= 1) return;

    Ttk_Box box{0, 0, win_w, win_h};
    auto* s = handle.get();
    if (!s) return;
    s->flush();
    uint8_t* pixels = s->data_ptr();
    size_t stride = s->stride();
    NativeBlit(tkwin_, drawable, box, pixels, stride, s->width(), s->height());
}

void NativeWidgetController::blit_surface(Surface& surf) {
    std::lock_guard<std::mutex> lock(mutex_);
    bound_surface_id_ = surf.surface_id();

    if (!tkwin_) return;
    if (Tk_WindowId(tkwin_) == None) {
        Tk_MakeWindowExist(tkwin_);
    }
    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    int win_w = Tk_Width(tkwin_);
    int win_h = Tk_Height(tkwin_);
    if (win_w <= 1 || win_h <= 1) return;

    Ttk_Box box{0, 0, win_w, win_h};
    surf.flush();
    uint8_t* pixels = surf.data_ptr();
    size_t stride = surf.stride();
    NativeBlit(tkwin_, drawable, box, pixels, stride, surf.width(), surf.height());
}

} // namespace tkblend
