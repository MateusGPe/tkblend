#include "blit_backend.h"

#if defined(__linux__) || defined(__unix__)
#if !defined(__APPLE__)

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <cstring>

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

    int put_w = (box.width < width) ? box.width : width;
    int put_h = (box.height < height) ? box.height : height;

    XPutImage(
        display,
        drawable,
        gc,
        ximage,
        0, 0,
        box.x, box.y,
        static_cast<unsigned int>(put_w),
        static_cast<unsigned int>(put_h)
    );

    Tk_FreeGC(display, gc);

    // CRITICAL: Detach pointer so XDestroyImage does NOT free Blend2D internal buffer
    ximage->data = nullptr;
    XDestroyImage(ximage);

    return true;
}

uint32_t ResolveAncestorBackground(Tk_Window tkwin, uint32_t fallback_argb) {
    if (!tkwin) return fallback_argb;

    Tk_Window curr = tkwin;
    while (curr) {
        const char* bg_val = Tk_GetOption(curr, "background", "Background");
        if (bg_val && bg_val[0] != '\0') {
            XColor* xc = Tk_GetColor(nullptr, curr, bg_val);
            if (xc) {
                uint32_t r = (xc->red >> 8) & 0xFF;
                uint32_t g = (xc->green >> 8) & 0xFF;
                uint32_t b = (xc->blue >> 8) & 0xFF;
                Tk_FreeColor(xc);
                return (0xFF000000u | (r << 16) | (g << 8) | b);
            }
        }
        curr = Tk_Parent(curr);
    }
    return fallback_argb;
}

} // namespace tkblend

#endif // !__APPLE__
#endif // __linux__ || __unix__
