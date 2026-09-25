#include "shadow_engine.hpp"
#include <cmath>
#include <algorithm>
#include <vector>

namespace tkblend {

ShadowEngine& ShadowEngine::instance() {
    static ShadowEngine instance;
    return instance;
}

void ShadowEngine::apply_3pass_box_blur(BLImageData& data, double blur_radius) {
    if (blur_radius <= 0.0) return;

    int w = static_cast<int>(data.size.w);
    int h = static_cast<int>(data.size.h);
    if (w <= 0 || h <= 0) return;

    int stride = static_cast<int>(data.stride);
    uint8_t* pixels = static_cast<uint8_t*>(data.pixel_data);

    // Compute standard 3-box approximation of Gaussian sigma
    double sigma = blur_radius / 2.0;
    double wIdeal = std::sqrt((12.0 * sigma * sigma / 3.0) + 1.0);
    int wl = static_cast<int>(std::floor(wIdeal));
    if (wl % 2 == 0) wl--;
    int wu = wl + 2;
    double mIdeal = (12.0 * sigma * sigma - 3.0 * wl * wl - 12.0 * wl - 9.0) / (-4.0 * wl - 4.0);
    int m = static_cast<int>(std::round(mIdeal));

    int box_r[3];
    for (int i = 0; i < 3; ++i) {
        int box_w = (i < m ? wl : wu);
        box_r[i] = std::max(1, (box_w - 1) / 2);
    }

    std::vector<uint8_t> temp(w * h * 4);

    // Perform 3 horizontal + vertical passes on 32-bit PRGB buffer
    for (int pass = 0; pass < 3; ++pass) {
        int r = box_r[pass];
        float inv_w = 1.0f / (2.0f * r + 1.0f);

        // Horizontal Pass: pixels -> temp
        for (int y = 0; y < h; ++y) {
            uint8_t* src_row = pixels + y * stride;
            uint8_t* dst_row = temp.data() + (y * w) * 4;

            int sum_b = src_row[0] * (r + 1);
            int sum_g = src_row[1] * (r + 1);
            int sum_r = src_row[2] * (r + 1);
            int sum_a = src_row[3] * (r + 1);

            for (int i = 0; i < r; ++i) {
                int cx = std::min(i, w - 1) * 4;
                sum_b += src_row[cx + 0];
                sum_g += src_row[cx + 1];
                sum_r += src_row[cx + 2];
                sum_a += src_row[cx + 3];
            }

            for (int x = 0; x < w; ++x) {
                int right_x = std::min(x + r, w - 1) * 4;
                int left_x = std::max(x - r - 1, 0) * 4;

                dst_row[x * 4 + 0] = static_cast<uint8_t>(sum_b * inv_w);
                dst_row[x * 4 + 1] = static_cast<uint8_t>(sum_g * inv_w);
                dst_row[x * 4 + 2] = static_cast<uint8_t>(sum_r * inv_w);
                dst_row[x * 4 + 3] = static_cast<uint8_t>(sum_a * inv_w);

                sum_b += src_row[right_x + 0] - src_row[left_x + 0];
                sum_g += src_row[right_x + 1] - src_row[left_x + 1];
                sum_r += src_row[right_x + 2] - src_row[left_x + 2];
                sum_a += src_row[right_x + 3] - src_row[left_x + 3];
            }
        }

        // Vertical Pass: temp -> pixels
        float inv_h = inv_w;
        for (int x = 0; x < w; ++x) {
            int sum_b = temp[(0 * w + x) * 4 + 0] * (r + 1);
            int sum_g = temp[(0 * w + x) * 4 + 1] * (r + 1);
            int sum_r = temp[(0 * w + x) * 4 + 2] * (r + 1);
            int sum_a = temp[(0 * w + x) * 4 + 3] * (r + 1);

            for (int i = 0; i < r; ++i) {
                int cy = std::min(i, h - 1);
                sum_b += temp[(cy * w + x) * 4 + 0];
                sum_g += temp[(cy * w + x) * 4 + 1];
                sum_r += temp[(cy * w + x) * 4 + 2];
                sum_a += temp[(cy * w + x) * 4 + 3];
            }

            for (int y = 0; y < h; ++y) {
                uint8_t* dst_ptr = pixels + y * stride + x * 4;
                int right_y = std::min(y + r, h - 1);
                int left_y = std::max(y - r - 1, 0);

                dst_ptr[0] = static_cast<uint8_t>(sum_b * inv_h);
                dst_ptr[1] = static_cast<uint8_t>(sum_g * inv_h);
                dst_ptr[2] = static_cast<uint8_t>(sum_r * inv_h);
                dst_ptr[3] = static_cast<uint8_t>(sum_a * inv_h);

                sum_b += temp[(right_y * w + x) * 4 + 0] - temp[(left_y * w + x) * 4 + 0];
                sum_g += temp[(right_y * w + x) * 4 + 1] - temp[(left_y * w + x) * 4 + 1];
                sum_r += temp[(right_y * w + x) * 4 + 2] - temp[(left_y * w + x) * 4 + 2];
                sum_a += temp[(right_y * w + x) * 4 + 3] - temp[(left_y * w + x) * 4 + 3];
            }
        }
    }
}

BLImage ShadowEngine::get_or_render_rounded_shadow(
    double w, double h, double rx, double ry,
    double blur_radius, double spread,
    const Color& shadow_color,
    int& out_pad_x, int& out_pad_y
) {
    int iw = static_cast<int>(std::round(w));
    int ih = static_cast<int>(std::round(h));
    int irx = static_cast<int>(std::round(rx));
    int iry = static_cast<int>(std::round(ry));
    int iblur = static_cast<int>(std::round(blur_radius * 10.0));
    int ispread = static_cast<int>(std::round(spread * 10.0));
    uint32_t col_u32 = shadow_color.to_u32();

    ShadowKey key{iw, ih, irx, iry, iblur, ispread, col_u32};

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = cache_map_.find(key);
    if (it != cache_map_.end()) {
        lru_list_.splice(lru_list_.begin(), lru_list_, it->second);
        out_pad_x = it->second->pad_x;
        out_pad_y = it->second->pad_y;
        return it->second->image;
    }

    // Render new shadow
    int pad = static_cast<int>(std::ceil(blur_radius * 2.5 + std::abs(spread) + 4.0));
    out_pad_x = pad;
    out_pad_y = pad;

    int mask_w = iw + static_cast<int>(std::round(spread * 2.0)) + pad * 2;
    int mask_h = ih + static_cast<int>(std::round(spread * 2.0)) + pad * 2;

    if (mask_w <= 0 || mask_h <= 0) {
        return BLImage();
    }

    BLImage shadow_img(mask_w, mask_h, BL_FORMAT_PRGB32);
    BLContext sctx(shadow_img);
    sctx.clear_all();

    double geom_x = pad - spread;
    double geom_y = pad - spread;
    double geom_w = w + spread * 2.0;
    double geom_h = h + spread * 2.0;
    double geom_rx = std::max(0.0, rx + spread);
    double geom_ry = std::max(0.0, ry + spread);

    sctx.set_fill_style(shadow_color.to_bl_rgba32());
    sctx.fill_round_rect(BLRoundRect(geom_x, geom_y, geom_w, geom_h, geom_rx, geom_ry));
    sctx.end();

    if (blur_radius > 0.1) {
        BLImageData img_data;
        shadow_img.make_mutable(&img_data);
        apply_3pass_box_blur(img_data, blur_radius);
    }

    size_t new_bytes = static_cast<size_t>(mask_w * mask_h * 4);

    // Evict old entries if entry count or byte limit exceeded
    while (!lru_list_.empty() && (lru_list_.size() >= max_cache_entries_ || current_cache_bytes_ + new_bytes > max_cache_bytes_)) {
        auto last = lru_list_.end();
        --last;
        current_cache_bytes_ = (current_cache_bytes_ >= last->bytes) ? (current_cache_bytes_ - last->bytes) : 0;
        cache_map_.erase(last->key);
        lru_list_.pop_back();
    }

    lru_list_.push_front(CachedShadow{key, shadow_img, pad, pad, new_bytes});
    current_cache_bytes_ += new_bytes;
    cache_map_[key] = lru_list_.begin();

    return shadow_img;
}

void ShadowEngine::clear_cache() {
    std::lock_guard<std::mutex> lock(mutex_);
    cache_map_.clear();
    lru_list_.clear();
    current_cache_bytes_ = 0;
}

size_t ShadowEngine::get_cache_size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return lru_list_.size();
}

size_t ShadowEngine::get_cache_bytes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_cache_bytes_;
}

void ShadowEngine::set_cache_limits(size_t max_entries, size_t max_bytes) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_cache_entries_ = std::max<size_t>(1, max_entries);
    max_cache_bytes_ = std::max<size_t>(1024 * 1024, max_bytes);
    while (!lru_list_.empty() && (lru_list_.size() > max_cache_entries_ || current_cache_bytes_ > max_cache_bytes_)) {
        auto last = lru_list_.end();
        --last;
        current_cache_bytes_ = (current_cache_bytes_ >= last->bytes) ? (current_cache_bytes_ - last->bytes) : 0;
        cache_map_.erase(last->key);
        lru_list_.pop_back();
    }
}

} // namespace tkblend
