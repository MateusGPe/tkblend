#include "blit_backend.h"

#if defined(_WIN32)

#include <windows.h>
#include <tkPlatDecls.h>
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
    if (!tkwin || !drawable || !pixelData) {
        return false;
    }
    if (width <= 0 || height <= 0 || box.width <= 0 || box.height <= 0) {
        return false;
    }

    TkWinDCState dcState;
    HDC hdc = TkWinGetDrawableDC(Tk_Display(tkwin), drawable, &dcState);
    if (!hdc) {
        return false;
    }

    BITMAPINFO bmi;
    std::memset(&bmi, 0, sizeof(BITMAPINFO));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height; // Top-down DIB layout
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    int put_w = (box.width < width) ? box.width : width;
    int put_h = (box.height < height) ? box.height : height;

    SetDIBitsToDevice(
        hdc,
        box.x, box.y,
        put_w, put_h,
        0, 0,
        0, static_cast<UINT>(height),
        pixelData,
        &bmi,
        DIB_RGB_COLORS
    );

    TkWinReleaseDrawableDC(drawable, hdc, &dcState);
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

#endif // _WIN32
