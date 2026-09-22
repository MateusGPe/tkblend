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

    int win_w = Tk_Width(tkwin);
    int win_h = Tk_Height(tkwin);
    if (win_w <= 0 || win_h <= 0) {
        TkWinReleaseDrawableDC(drawable, hdc, &dcState);
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
        TkWinReleaseDrawableDC(drawable, hdc, &dcState);
        return true; // Completely clipped out
    }

    SetDIBitsToDevice(
        hdc,
        dst_x, dst_y,
        req_w, req_h,
        src_x, src_y,
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

#endif // _WIN32
