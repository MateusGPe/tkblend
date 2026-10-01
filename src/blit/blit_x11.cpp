#include "blit_backend.h"

#if defined(__linux__) || defined(__unix__)
#if !defined(__APPLE__)

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <cstring>
#include <string>

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

    BlitClipResult clip = ComputeBlitClip(tkwin, box, width, height);
    if (!clip.visible) {
        Tk_FreeGC(display, gc);
        ximage->data = nullptr;
        XDestroyImage(ximage);
        return true; // Completely clipped out
    }

    XPutImage(
        display,
        drawable,
        gc,
        ximage,
        clip.src_x, clip.src_y,
        clip.dst_x, clip.dst_y,
        static_cast<unsigned int>(clip.req_w),
        static_cast<unsigned int>(clip.req_h)
    );

    XFlush(display);

    Tk_FreeGC(display, gc);

    // CRITICAL: Detach pointer so XDestroyImage does NOT free Blend2D internal buffer
    ximage->data = nullptr;
    XDestroyImage(ximage);

    return true;
}

} // namespace tkblend

#endif // !__APPLE__
#endif // __linux__ || __unix__
