#include "blit_backend.h"

#if defined(_WIN32)

#include <windows.h>
#include <tkPlatDecls.h>
#include <cstring>

struct TkWinDCState {
    HPALETTE palette;
    int bkmode;
};

extern "C" {
EXTERN HDC TkWinGetDrawableDC(Display* display, Drawable drawable, TkWinDCState* state);
EXTERN void TkWinReleaseDrawableDC(Drawable drawable, HDC dc, TkWinDCState* state);
}

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

    BlitClipResult clip = ComputeBlitClip(tkwin, box, width, height);
    if (!clip.visible) {
        TkWinReleaseDrawableDC(drawable, hdc, &dcState);
        return true; // Completely clipped out
    }

    SetDIBitsToDevice(
        hdc,
        clip.dst_x, clip.dst_y,
        clip.req_w, clip.req_h,
        clip.src_x, clip.src_y,
        0, static_cast<UINT>(height),
        pixelData,
        &bmi,
        DIB_RGB_COLORS
    );

    TkWinReleaseDrawableDC(drawable, hdc, &dcState);
    return true;
}

} // namespace tkblend

#endif // _WIN32
