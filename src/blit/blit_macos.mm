#include "blit_backend.h"

#if defined(__APPLE__)

#import <Cocoa/Cocoa.h>
#import <CoreGraphics/CoreGraphics.h>
#include <dlfcn.h>

namespace {
typedef CGContextRef (*TkMacOSXGetCGContextForDrawableFunc)(Drawable);

static TkMacOSXGetCGContextForDrawableFunc GetTkMacOSXGetCGContextForDrawableFn() {
    static TkMacOSXGetCGContextForDrawableFunc fn = nullptr;
    static bool resolved = false;
    if (!resolved) {
        fn = (TkMacOSXGetCGContextForDrawableFunc)dlsym(RTLD_DEFAULT, "TkMacOSXGetCGContextForDrawable");
        resolved = true;
    }
    return fn;
}
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

    auto tk_cgcontext_fn = GetTkMacOSXGetCGContextForDrawableFn();
    if (!tk_cgcontext_fn) {
        return false;
    }

    CGContextRef context = tk_cgcontext_fn(drawable);
    if (!context) {
        return false;
    }

    BlitClipResult clip = ComputeBlitClip(tkwin, box, width, height);
    if (!clip.visible) {
        return true; // Completely clipped out
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
        
        CGRect destRect = CGRectMake(clip.dst_x, clip.dst_y, clip.req_w, clip.req_h);
        // Tk coordinate system on macOS is top-left origin; Flip context vertically for CoreGraphics
        CGContextTranslateCTM(context, destRect.origin.x, destRect.origin.y + destRect.size.height);
        CGContextScaleCTM(context, 1.0, -1.0);

        if (clip.src_x == 0 && clip.src_y == 0 && clip.req_w == width && clip.req_h == height) {
            CGContextDrawImage(context, CGRectMake(0, 0, destRect.size.width, destRect.size.height), cgImage);
        } else {
            CGRect cropRect = CGRectMake(clip.src_x, clip.src_y, clip.req_w, clip.req_h);
            CGImageRef cropped = CGImageCreateWithImageInRect(cgImage, cropRect);
            if (cropped) {
                CGContextDrawImage(context, CGRectMake(0, 0, destRect.size.width, destRect.size.height), cropped);
                CGImageRelease(cropped);
            }
        }
        
        CGContextRestoreGState(context);
        CGImageRelease(cgImage);
    }

    CGColorSpaceRelease(colorSpace);
    CGDataProviderRelease(dataProvider);

    return true;
}

} // namespace tkblend

#endif // __APPLE__
