#include "blit_backend.h"

#if defined(__linux__) || defined(__unix__)
#if !defined(__APPLE__)

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <cstring>
#include <string>
#include "../theme/theme_engine.h"

namespace tkblend {

bool NativeBlit(
    Tk_Window tkwin,
    Drawable drawable,
    const Ttk_Box& box,
    const uint8_t* pixelData,
    size_t stride,
    int width,
    int height
) {
    if (!tkwin || drawable == None || !pixelData) {
        return false;
    }
    if (width <= 0 || height <= 0 || box.width <= 0 || box.height <= 0) {
        return false;
    }

    Display* display = Tk_Display(tkwin);
    if (!display) {
        return false;
    }

    Visual* visual = Tk_Visual(tkwin);
    int depth = Tk_Depth(tkwin);
    if (!visual || depth <= 0) {
        return false;
    }

    // Allocate XImage with Blend2D buffer (Zero-copy wrapping)
    XImage* ximage = XCreateImage(
        display,
        visual,
        static_cast<unsigned int>(depth),
        ZPixmap,
        0,
        reinterpret_cast<char*>(const_cast<uint8_t*>(pixelData)),
        static_cast<unsigned int>(width),
        static_cast<unsigned int>(height),
        32,
        static_cast<int>(stride)
    );

    if (!ximage) {
        return false;
    }

    // Default byte-order setup matching 32-bit PRGB/ARGB
    ximage->bits_per_pixel = 32;
    #if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    ximage->byte_order = LSBFirst;
    ximage->bitmap_bit_order = LSBFirst;
    #else
    ximage->byte_order = MSBFirst;
    ximage->bitmap_bit_order = MSBFirst;
    #endif

    // Acquire GC for Tk drawable
    XGCValues gcValues;
    std::memset(&gcValues, 0, sizeof(gcValues));
    gcValues.graphics_exposures = False;
    GC gc = Tk_GetGC(tkwin, GCGraphicsExposures, &gcValues);

    int win_w = Tk_Width(tkwin);
    int win_h = Tk_Height(tkwin);
    if (win_w <= 0 || win_h <= 0) {
        return false;
    }

    int dst_x = box.x;
    int dst_y = box.y;
    int req_w = (box.width < width) ? box.width : width;
    int req_h = (box.height < height) ? box.height : height;
    int src_x = 0;
    int src_y = 0;

    // 4-sided clipping against window boundaries
    if (dst_x < 0) {
        src_x += -dst_x;
        req_w -= -dst_x;
        dst_x = 0;
    }
    if (dst_y < 0) {
        src_y += -dst_y;
        req_h -= -dst_y;
        dst_y = 0;
    }
    if (dst_x + req_w > win_w) {
        req_w = win_w - dst_x;
    }
    if (dst_y + req_h > win_h) {
        req_h = win_h - dst_y;
    }

    // Clip against source image dimensions
    if (src_x + req_w > width) {
        req_w = width - src_x;
    }
    if (src_y + req_h > height) {
        req_h = height - src_y;
    }

    if (req_w <= 0 || req_h <= 0 || src_x >= width || src_y >= height) {
        return true; // Completely clipped out, nothing to draw
    }

    XPutImage(
        display,
        drawable,
        gc,
        ximage,
        src_x, src_y,
        dst_x, dst_y,
        static_cast<unsigned int>(req_w),
        static_cast<unsigned int>(req_h)
    );

    Tk_FreeGC(display, gc);

    // CRITICAL: Detach pointer so XDestroyImage does NOT free Blend2D internal buffer
    ximage->data = nullptr;
    XDestroyImage(ximage);

    return true;
}

uint32_t ResolveAncestorBackground(Tk_Window tkwin, uint32_t fallback_argb) {
    if (!tkwin) return fallback_argb;

    const auto& cfg = ThemeEngine::instance().config();
    Tk_Window curr = tkwin;
    while (curr) {
        const char* className = Tk_Class(curr);
        if (className) {
            std::string cls(className);
            if (cls == "TLabelframe" || cls == "Labelframe" ||
                cls.find("Card") != std::string::npos ||
                cls.find("Notebook") != std::string::npos ||
                cls.find("Panedwindow") != std::string::npos) {
                return cfg.card_bg;
            }
        }
        curr = Tk_Parent(curr);
    }
    return cfg.bg_color;
}

} // namespace tkblend

#endif // !__APPLE__
#endif // __linux__ || __unix__
