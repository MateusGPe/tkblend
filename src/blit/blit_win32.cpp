#include "blit_backend.h"

#if defined(_WIN32)

#include <windows.h>
#include <tkPlatDecls.h>
#include <cstring>

struct TkWinDCState {
    HPALETTE palette;
    int bkmode;
};

#if !defined(TKBLEND_PURE_STUBS)
extern "C" {
EXTERN HDC TkWinGetDrawableDC(Display* display, Drawable drawable, TkWinDCState* state);
EXTERN void TkWinReleaseDrawableDC(Drawable drawable, HDC dc, TkWinDCState* state);
}
#endif

namespace tkblend {

namespace {

struct Win32DCHandle {
    HDC hdc{nullptr};
    HWND hwnd{nullptr};
    bool used_tk_release{false};
    TkWinDCState dc_state{};
};

static inline Win32DCHandle AcquireDrawableDC(Tk_Window tkwin, Drawable drawable) {
    Win32DCHandle res;

    // 1. Primary path (Pure Tk Stubs): Retrieve HWND via public stub table
    HWND hwnd = Tk_GetHWND(drawable);
    if (hwnd) {
        res.hwnd = hwnd;
        res.hdc = GetDC(hwnd);
        if (res.hdc) {
            return res;
        }
    }

#if !defined(TKBLEND_PURE_STUBS)
    // Direct-link dev mode: call internal TkWinGetDrawableDC directly
    res.hdc = TkWinGetDrawableDC(Tk_Display(tkwin), drawable, &res.dc_state);
    if (res.hdc) {
        res.used_tk_release = true;
        return res;
    }
#else
    // 2. Fallback path (Off-screen pixmaps or non-HWND drawables):
    // Dynamically query loaded Tk runtime in host process (e.g. tk90.dll, tk86t.dll)
    // without introducing any compile-time or load-time PE DLL dependency.
    using PFN_TkWinGetDrawableDC = HDC (*)(Display*, Drawable, TkWinDCState*);
    static PFN_TkWinGetDrawableDC s_fnGetDC = []() -> PFN_TkWinGetDrawableDC {
        const char* const candidate_modules[] = {
            "tk90.dll", "tk86t.dll", "tk86.dll", "tk.dll"
        };
        for (const char* mod_name : candidate_modules) {
            HMODULE h = GetModuleHandleA(mod_name);
            if (h) {
                auto fn = reinterpret_cast<PFN_TkWinGetDrawableDC>(
                    GetProcAddress(h, "TkWinGetDrawableDC")
                );
                if (fn) return fn;
            }
        }
        return nullptr;
    }();

    if (s_fnGetDC) {
        res.hdc = s_fnGetDC(Tk_Display(tkwin), drawable, &res.dc_state);
        if (res.hdc) {
            res.used_tk_release = true;
            return res;
        }
    }
#endif

    return res;
}

static inline void ReleaseDrawableDC(Drawable drawable, const Win32DCHandle& handle) {
    if (!handle.hdc) return;

    if (handle.hwnd && !handle.used_tk_release) {
        ReleaseDC(handle.hwnd, handle.hdc);
        return;
    }

#if !defined(TKBLEND_PURE_STUBS)
    if (handle.used_tk_release) {
        TkWinReleaseDrawableDC(drawable, handle.hdc, const_cast<TkWinDCState*>(&handle.dc_state));
    }
#else
    if (handle.used_tk_release) {
        using PFN_TkWinReleaseDrawableDC = void (*)(Drawable, HDC, TkWinDCState*);
        static PFN_TkWinReleaseDrawableDC s_fnReleaseDC = []() -> PFN_TkWinReleaseDrawableDC {
            const char* const candidate_modules[] = {
                "tk90.dll", "tk86t.dll", "tk86.dll", "tk.dll"
            };
            for (const char* mod_name : candidate_modules) {
                HMODULE h = GetModuleHandleA(mod_name);
                if (h) {
                    auto fn = reinterpret_cast<PFN_TkWinReleaseDrawableDC>(
                        GetProcAddress(h, "TkWinReleaseDrawableDC")
                    );
                    if (fn) return fn;
                }
            }
            return nullptr;
        }();

        if (s_fnReleaseDC) {
            s_fnReleaseDC(drawable, handle.hdc, const_cast<TkWinDCState*>(&handle.dc_state));
        }
    }
#endif
}

} // anonymous namespace

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

    Win32DCHandle dcHandle = AcquireDrawableDC(tkwin, drawable);
    if (!dcHandle.hdc) {
        return false;
    }

    BITMAPINFO bmi;
    std::memset(&bmi, 0, sizeof(BITMAPINFO));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    // In GDI DIBs, each scanline pitch is derived from biWidth: ((biWidth * 32 + 31) / 32) * 4 = biWidth * 4 bytes.
    // Blend2D allocates buffers with SIMD-aligned stride (e.g. 16, 32, or 64 bytes).
    // Setting biWidth to stride / 4 ensures GDI advances rows matching Blend2D's actual memory pitch,
    // while clip.req_w dictates the actual drawn region.
    LONG stride_pixels = (stride > 0 && (stride % 4 == 0))
        ? static_cast<LONG>(stride / 4)
        : static_cast<LONG>(width);
    bmi.bmiHeader.biWidth = stride_pixels;
    bmi.bmiHeader.biHeight = -height; // Top-down DIB layout
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    BlitClipResult clip = ComputeBlitClip(tkwin, box, width, height);
    if (!clip.visible) {
        ReleaseDrawableDC(drawable, dcHandle);
        return true; // Completely clipped out
    }

    SetDIBitsToDevice(
        dcHandle.hdc,
        clip.dst_x, clip.dst_y,
        clip.req_w, clip.req_h,
        clip.src_x, clip.src_y,
        0, static_cast<UINT>(height),
        pixelData,
        &bmi,
        DIB_RGB_COLORS
    );

    ReleaseDrawableDC(drawable, dcHandle);
    return true;
}

} // namespace tkblend

#endif // _WIN32
