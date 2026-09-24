#include "window_shape.hpp"

#if defined(__linux__) || defined(__FreeBSD__) || (defined(__unix__) && !defined(__APPLE__))
#include <X11/Xlib.h>
#include <X11/extensions/shape.h>
#include <cmath>
#include <vector>
#include <algorithm>
#include <mutex>

namespace tkblend {

namespace {

struct X11ShapeContext {
    Display* dpy = nullptr;
    bool supported = false;
    std::mutex mutex;

    X11ShapeContext() {
        dpy = XOpenDisplay(nullptr);
        if (dpy) {
            int event_base = 0, error_base = 0;
            Bool ext_supported = XShapeQueryExtension(dpy, &event_base, &error_base);
            supported = (ext_supported == True);
        }
    }

    ~X11ShapeContext() {
        if (dpy) {
            XCloseDisplay(dpy);
            dpy = nullptr;
        }
    }
};

static X11ShapeContext& get_x11_context() {
    static X11ShapeContext ctx;
    return ctx;
}

} // anonymous namespace

bool is_window_shaping_supported() {
    auto& ctx = get_x11_context();
    return (ctx.dpy != nullptr && ctx.supported);
}

bool apply_round_rect_shape(uint64_t window_id, int width, int height, double rx, double ry) {
    if (window_id == 0 || width <= 0 || height <= 0) {
        return false;
    }
    if (rx <= 0.0 || ry <= 0.0) {
        return clear_window_shape(window_id);
    }

    auto& ctx = get_x11_context();
    if (!ctx.dpy || !ctx.supported) {
        return false;
    }

    double rx_clamped = std::min(rx, static_cast<double>(width) / 2.0);
    double ry_clamped = std::min(ry, static_cast<double>(height) / 2.0);

    int ry_int = static_cast<int>(std::ceil(ry_clamped));
    int top_count = std::min(ry_int, height);
    int bot_start = std::max(top_count, height - ry_int);

    std::vector<XRectangle> rects;
    rects.reserve(top_count + (height - bot_start) + 1);

    // 1. Top rounded corner spans
    for (int y = 0; y < top_count; ++y) {
        double dy_ratio = (ry_clamped - y) / ry_clamped;
        int dx = static_cast<int>(std::ceil(rx_clamped * (1.0 - std::sqrt(std::max(0.0, 1.0 - dy_ratio * dy_ratio)))));
        short span_w = static_cast<short>(std::max(0, width - 2 * dx));
        rects.push_back(XRectangle{static_cast<short>(dx), static_cast<short>(y), static_cast<unsigned short>(span_w), 1});
    }

    // 2. Middle full-width span (coalesced into a single rectangle)
    if (bot_start > top_count) {
        short mid_h = static_cast<short>(bot_start - top_count);
        rects.push_back(XRectangle{0, static_cast<short>(top_count), static_cast<unsigned short>(width), static_cast<unsigned short>(mid_h)});
    }

    // 3. Bottom rounded corner spans
    for (int y = bot_start; y < height; ++y) {
        double dy_ratio = (y - (height - ry_clamped) + 1) / ry_clamped;
        int dx = static_cast<int>(std::ceil(rx_clamped * (1.0 - std::sqrt(std::max(0.0, 1.0 - dy_ratio * dy_ratio)))));
        short span_w = static_cast<short>(std::max(0, width - 2 * dx));
        rects.push_back(XRectangle{static_cast<short>(dx), static_cast<short>(y), static_cast<unsigned short>(span_w), 1});
    }

    {
        std::lock_guard<std::mutex> lock(ctx.mutex);
        XShapeCombineRectangles(
            ctx.dpy,
            static_cast<Window>(window_id),
            ShapeBounding,
            0,
            0,
            rects.data(),
            static_cast<int>(rects.size()),
            ShapeSet,
            Unsorted
        );
        XFlush(ctx.dpy);
    }
    return true;
}

bool clear_window_shape(uint64_t window_id) {
    if (window_id == 0) {
        return false;
    }
    auto& ctx = get_x11_context();
    if (!ctx.dpy || !ctx.supported) {
        return false;
    }

    {
        std::lock_guard<std::mutex> lock(ctx.mutex);
        XShapeCombineMask(
            ctx.dpy,
            static_cast<Window>(window_id),
            ShapeBounding,
            0,
            0,
            None,
            ShapeSet
        );
        XFlush(ctx.dpy);
    }
    return true;
}

} // namespace tkblend

#elif defined(_WIN32)
#include <windows.h>

namespace tkblend {

bool is_window_shaping_supported() {
    return true;
}

bool apply_round_rect_shape(uint64_t window_id, int width, int height, double rx, double ry) {
    if (window_id == 0 || width <= 0 || height <= 0) {
        return false;
    }
    if (rx <= 0.0 || ry <= 0.0) {
        return clear_window_shape(window_id);
    }

    HWND hwnd = reinterpret_cast<HWND>(static_cast<uintptr_t>(window_id));
    HRGN hrgn = CreateRoundRectRgn(
        0,
        0,
        width + 1,
        height + 1,
        static_cast<int>(rx * 2.0),
        static_cast<int>(ry * 2.0)
    );
    if (!hrgn) {
        return false;
    }
    if (!SetWindowRgn(hwnd, hrgn, TRUE)) {
        DeleteObject(hrgn);
        return false;
    }
    return true;
}

bool clear_window_shape(uint64_t window_id) {
    if (window_id == 0) {
        return false;
    }
    HWND hwnd = reinterpret_cast<HWND>(static_cast<uintptr_t>(window_id));
    return SetWindowRgn(hwnd, NULL, TRUE) != 0;
}

} // namespace tkblend

#elif defined(__APPLE__)
#import <Cocoa/Cocoa.h>

// Note: Under ARC builds (-fobjc-arc), __bridge is a non-retaining borrowed reference cast.
// The caller (Tk/Tkinter) manages the lifetime of the native NSView window hierarchy.
// @autoreleasepool ensures any transient ObjC allocations during property access are released.
namespace tkblend {

bool is_window_shaping_supported() {
    return true;
}

bool apply_round_rect_shape(uint64_t window_id, int width, int height, double rx, double ry) {
    if (window_id == 0) {
        return false;
    }
    @autoreleasepool {
        NSView* view = (__bridge NSView*)(void*)(uintptr_t)window_id;
        if (!view || ![view isKindOfClass:[NSView class]]) {
            return false;
        }
        view.wantsLayer = YES;
        view.layer.masksToBounds = YES;
        view.layer.cornerRadius = static_cast<CGFloat>(rx);
        return true;
    }
}

bool clear_window_shape(uint64_t window_id) {
    if (window_id == 0) {
        return false;
    }
    @autoreleasepool {
        NSView* view = (__bridge NSView*)(void*)(uintptr_t)window_id;
        if (!view || ![view isKindOfClass:[NSView class]]) {
            return false;
        }
        view.layer.masksToBounds = NO;
        view.layer.cornerRadius = 0.0;
        return true;
    }
}

} // namespace tkblend

#else

namespace tkblend {

bool is_window_shaping_supported() {
    return false;
}

bool apply_round_rect_shape(uint64_t, int, int, double, double) {
    return false;
}

bool clear_window_shape(uint64_t) {
    return false;
}

} // namespace tkblend

#endif
