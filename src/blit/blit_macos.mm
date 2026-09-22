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
        
        CGRect destRect = CGRectMake(dst_x, dst_y, req_w, req_h);
        // Tk coordinate system on macOS is top-left origin; Flip context vertically for CoreGraphics
        CGContextTranslateCTM(context, destRect.origin.x, destRect.origin.y + destRect.size.height);
        CGContextScaleCTM(context, 1.0, -1.0);

        if (src_x == 0 && src_y == 0 && req_w == width && req_h == height) {
            CGContextDrawImage(context, CGRectMake(0, 0, destRect.size.width, destRect.size.height), cgImage);
        } else {
            CGRect cropRect = CGRectMake(src_x, src_y, req_w, req_h);
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

#endif // __APPLE__
