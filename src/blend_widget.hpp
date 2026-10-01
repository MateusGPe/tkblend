#pragma once

#include "tk_compat.h"
#include <blend2d.h>
#include <cstdint>
#include <string>
#include <mutex>
#include <memory>

namespace tkblend {

class Surface;

class BlendWidget {
public:
    static std::shared_ptr<BlendWidget> attach(
        Tcl_Interp* interp,
        const std::string& widget_path,
        Surface* surface = nullptr
    );

    BlendWidget(Tcl_Interp* interp, Tk_Window tkwin, const std::string& widget_path, Surface* surface);
    ~BlendWidget();

    // Disable copy
    BlendWidget(const BlendWidget&) = delete;
    BlendWidget& operator=(const BlendWidget&) = delete;

    void set_surface(Surface* surface);
    Surface* get_surface() const { return surface_; }

    Tk_Window tkwin() const { return tkwin_; }
    const std::string& widget_path() const { return widget_path_; }
    int width() const { return width_; }
    int height() const { return height_; }

    void paint();
    void present();
    void resize(int width, int height);
    void detach();

private:
    static void WidgetEventProc(ClientData clientData, XEvent* eventPtr);
    static void IdlePaintProc(ClientData clientData);
    void setup_window_subclass();
    void restore_window_subclass();

    Tcl_Interp* interp_{nullptr};
    Tk_Window tkwin_{nullptr};
    std::string widget_path_;
    Surface* surface_{nullptr};
    int width_{1};
    int height_{1};
    bool is_destroyed_{false};
    mutable std::mutex mutex_;

#if defined(_WIN32)
    HWND hwnd_{nullptr};
    WNDPROC orig_wndproc_{nullptr};
    static LRESULT CALLBACK SubclassWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
#endif
};

} // namespace tkblend
