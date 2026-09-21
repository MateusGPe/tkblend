#include "blit_backend.h"

#if defined(__APPLE__)

#import <Cocoa/Cocoa.h>
#import <CoreGraphics/CoreGraphics.h>

extern "C" {
    CGContextRef TkMacOSXGetCGContextForDrawable(Drawable drawable);
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

    CGContextRef context = TkMacOSXGetCGContextForDrawable(drawable);
    if (!context) {
        return false;
    }

    CGDataProviderRef dataProvider = CGDataProviderCreateWithData(
        nullptr,
        pixelData,
        stride * height,
        nullptr
    );
    if (!dataProvider) {
        return false;
    }

    CGColorSpaceRef colorSpace = CGColorSpaceCreateDeviceRGB();
    CGImageRef cgImage = CGImageCreate(
        width,
        height,
        8,
        32,
        stride,
        colorSpace,
        kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little,
        dataProvider,
        nullptr,
        false,
        kCGRenderingIntentDefault
    );

    if (cgImage) {
        CGContextSaveGState(context);
        
        CGRect destRect = CGRectMake(box.x, box.y, box.width, box.height);
        // Tk coordinate system on macOS is top-left origin; Flip context vertically for CoreGraphics
        CGContextTranslateCTM(context, destRect.origin.x, destRect.origin.y + destRect.size.height);
        CGContextScaleCTM(context, 1.0, -1.0);
        
        CGContextDrawImage(context, CGRectMake(0, 0, destRect.size.width, destRect.size.height), cgImage);
        
        CGContextRestoreGState(context);
        CGImageRelease(cgImage);
    }

    CGColorSpaceRelease(colorSpace);
    CGDataProviderRelease(dataProvider);

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

#endif // __APPLE__
