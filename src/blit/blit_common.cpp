#include "blit_backend.h"
#include <string>

namespace tkblend {

BlitClipResult ComputeBlitClip(
    Tk_Window tkwin,
    const Ttk_Box& box,
    int width,
    int height
) {
    BlitClipResult res;
    if (!tkwin || width <= 0 || height <= 0 || box.width <= 0 || box.height <= 0) {
        return res;
    }

    int win_w = Tk_Width(tkwin);
    int win_h = Tk_Height(tkwin);
    if (win_w <= 0 || win_h <= 0) {
        return res;
    }

    res.dst_x = box.x;
    res.dst_y = box.y;
    res.req_w = (box.width < width) ? box.width : width;
    res.req_h = (box.height < height) ? box.height : height;
    res.src_x = 0;
    res.src_y = 0;

    // 4-sided clipping against window boundaries
    if (res.dst_x < 0) {
        res.src_x += -res.dst_x;
        res.req_w -= -res.dst_x;
        res.dst_x = 0;
    }
    if (res.dst_y < 0) {
        res.src_y += -res.dst_y;
        res.req_h -= -res.dst_y;
        res.dst_y = 0;
    }
    if (res.dst_x + res.req_w > win_w) {
        res.req_w = win_w - res.dst_x;
    }
    if (res.dst_y + res.req_h > win_h) {
        res.req_h = win_h - res.dst_y;
    }

    // Clip against source image dimensions
    if (res.src_x + res.req_w > width) {
        res.req_w = width - res.src_x;
    }
    if (res.src_y + res.req_h > height) {
        res.req_h = height - res.src_y;
    }

    if (res.req_w <= 0 || res.req_h <= 0 || res.src_x >= width || res.src_y >= height) {
        res.visible = false;
        return res;
    }

    res.visible = true;
    return res;
}

uint32_t ResolveAncestorBackground(Tk_Window tkwin, uint32_t fallback_argb) {
    return fallback_argb;
}

} // namespace tkblend
