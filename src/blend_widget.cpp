#include "blend_widget.hpp"
#include "surface.hpp"
#include "blit/blit_backend.h"
#include <iostream>
#include <stdexcept>
#include <unordered_map>

namespace tkblend {

namespace {
    std::mutex g_widget_map_mutex;
    std::unordered_map<Tk_Window, BlendWidget*> g_widget_map;
}

std::shared_ptr<BlendWidget> BlendWidget::attach(
    Tcl_Interp* interp,
    const std::string& widget_path,
    Surface* surface
) {
    if (!interp) {
        throw std::invalid_argument("Invalid Tcl_Interp pointer");
    }
    if (!EnsureTkStubs(interp)) {
        throw std::runtime_error("Failed to initialize Tcl/Tk stubs");
    }

    Tk_Window main_win = Tk_MainWindow(interp);
    if (!main_win) {
        throw std::runtime_error("Tk_MainWindow returned null");
    }

    Tk_Window tkwin = Tk_NameToWindow(interp, widget_path.c_str(), main_win);
    if (!tkwin) {
        throw std::runtime_error("Tk_NameToWindow failed for widget: " + widget_path);
    }

    // Force native window creation
    Tk_MakeWindowExist(tkwin);

    // Suppress Tk native background clearing
    Tk_SetWindowBackgroundPixmap(tkwin, None);

    auto widget = std::make_shared<BlendWidget>(interp, tkwin, widget_path, surface);
    return widget;
}

BlendWidget::BlendWidget(
    Tcl_Interp* interp,
    Tk_Window tkwin,
    const std::string& widget_path,
    Surface* surface
)
    : interp_(interp),
      tkwin_(tkwin),
      widget_path_(widget_path),
      surface_(surface)
{
    int w = Tk_Width(tkwin_);
    int h = Tk_Height(tkwin_);
    if (w <= 0) w = Tk_ReqWidth(tkwin_);
    if (h <= 0) h = Tk_ReqHeight(tkwin_);
    width_ = (w > 0) ? w : 1;
    height_ = (h > 0) ? h : 1;

    {
        std::lock_guard<std::mutex> lock(g_widget_map_mutex);
        g_widget_map[tkwin_] = this;
    }

    setup_window_subclass();

    Tk_CreateEventHandler(
        tkwin_,
        ExposureMask | StructureNotifyMask,
        BlendWidget::WidgetEventProc,
        static_cast<ClientData>(this)
    );

    if (surface_) {
        surface_->set_blend_widget(this);
        surface_->resize(width_, height_);
    }
}

BlendWidget::~BlendWidget() {
    detach();
}

void BlendWidget::set_surface(Surface* surface) {
    std::lock_guard<std::mutex> lock(mutex_);
    surface_ = surface;
    if (surface_) {
        surface_->set_blend_widget(this);
        surface_->resize(width_, height_);
    }
}

void BlendWidget::detach() {
    Tcl_CancelIdleCall(BlendWidget::IdlePaintProc, static_cast<ClientData>(this));
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_destroyed_) return;
    is_destroyed_ = true;

    restore_window_subclass();

    if (tkwin_) {
        Tk_DeleteEventHandler(
            tkwin_,
            ExposureMask | StructureNotifyMask,
            BlendWidget::WidgetEventProc,
            static_cast<ClientData>(this)
        );

        {
            std::lock_guard<std::mutex> map_lock(g_widget_map_mutex);
            g_widget_map.erase(tkwin_);
        }
        tkwin_ = nullptr;
    }

    if (surface_) {
        surface_->set_blend_widget(nullptr);
        surface_ = nullptr;
    }
}

void BlendWidget::IdlePaintProc(ClientData cd) {
    BlendWidget* w = static_cast<BlendWidget*>(cd);
    if (w) {
        w->paint();
    }
}

void BlendWidget::WidgetEventProc(ClientData clientData, XEvent* eventPtr) {
    BlendWidget* self = static_cast<BlendWidget*>(clientData);
    if (!self || self->is_destroyed_) return;

    if (eventPtr->type == Expose) {
        if (eventPtr->xexpose.count == 0) {
            Tcl_CancelIdleCall(BlendWidget::IdlePaintProc, static_cast<ClientData>(self));
            Tcl_DoWhenIdle(BlendWidget::IdlePaintProc, static_cast<ClientData>(self));
        }
    } else if (eventPtr->type == ConfigureNotify) {
        int newW = eventPtr->xconfigure.width;
        int newH = eventPtr->xconfigure.height;
        if (newW > 0 && newH > 0 && (newW != self->width_ || newH != self->height_)) {
            self->resize(newW, newH);
        }
    } else if (eventPtr->type == DestroyNotify) {
        self->detach();
    }
}

void BlendWidget::resize(int width, int height) {
    if (width <= 0 || height <= 0 || is_destroyed_) return;

    Surface* surf_to_resize = nullptr;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        width_ = width;
        height_ = height;
        surf_to_resize = surface_;
    }

    if (surf_to_resize) {
        surf_to_resize->resize(width, height);
    }
}

void BlendWidget::paint() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_destroyed_ || !tkwin_ || !surface_) return;

    if (!Tk_IsMapped(tkwin_)) return;

    Drawable drawable = Tk_WindowId(tkwin_);
    if (drawable == None) return;

    surface_->flush();

    BLImageData imgData;
    if (!surface_->get_image_data(&imgData)) return;

    Ttk_Box box{0, 0, width_, height_};
    NativeBlit(
        tkwin_,
        drawable,
        box,
        static_cast<const uint8_t*>(imgData.pixel_data),
        imgData.stride,
        static_cast<int>(imgData.size.w),
        static_cast<int>(imgData.size.h)
    );
}

void BlendWidget::present() {
    paint();
}

void BlendWidget::setup_window_subclass() {
#if defined(_WIN32)
    if (!tkwin_) return;
    HWND hwnd = Tk_GetHWND(Tk_WindowId(tkwin_));
    if (hwnd) {
        hwnd_ = hwnd;
        SetPropW(hwnd, L"TkBlendWidget", reinterpret_cast<HANDLE>(this));
        orig_wndproc_ = reinterpret_cast<WNDPROC>(
            SetWindowLongPtrW(hwnd, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(SubclassWndProc))
        );
    }
#endif
}

void BlendWidget::restore_window_subclass() {
#if defined(_WIN32)
    if (hwnd_ && orig_wndproc_) {
        SetWindowLongPtrW(hwnd_, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(orig_wndproc_));
        RemovePropW(hwnd_, L"TkBlendWidget");
        orig_wndproc_ = nullptr;
        hwnd_ = nullptr;
    }
#endif
}

#if defined(_WIN32)
LRESULT CALLBACK BlendWidget::SubclassWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    BlendWidget* self = reinterpret_cast<BlendWidget*>(GetPropW(hwnd, L"TkBlendWidget"));
    if (msg == WM_ERASEBKGND) {
        return 1; // Suppress background erasing
    }
    if (self && self->orig_wndproc_) {
        return CallWindowProcW(self->orig_wndproc_, hwnd, msg, wParam, lParam);
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}
#endif

} // namespace tkblend
