#pragma once

#include "color.hpp"
#include <blend2d.h>
#include <cstdint>
#include <list>
#include <unordered_map>
#include <mutex>

namespace tkblend {

// Fast Separable 3-Pass Box Blur & Shadow Engine
class ShadowEngine {
public:
    static ShadowEngine& instance();

    void apply_3pass_box_blur(BLImageData& data, double blur_radius);
    BLImage get_or_render_rounded_shadow(
        double w, double h, double rx, double ry,
        double blur_radius, double spread,
        const Color& shadow_color,
        int& out_pad_x, int& out_pad_y
    );

private:
    ShadowEngine() = default;

    struct ShadowKey {
        int w, h, rx, ry, blur_radius_10x, spread_10x;
        uint32_t color_u32;

        bool operator==(const ShadowKey& o) const {
            return w == o.w && h == o.h && rx == o.rx && ry == o.ry &&
                   blur_radius_10x == o.blur_radius_10x &&
                   spread_10x == o.spread_10x &&
                   color_u32 == o.color_u32;
        }
    };

    struct ShadowKeyHash {
        std::size_t operator()(const ShadowKey& k) const {
            std::size_t h1 = std::hash<int>()(k.w) ^ (std::hash<int>()(k.h) << 1);
            std::size_t h2 = std::hash<int>()(k.rx) ^ (std::hash<int>()(k.ry) << 1);
            std::size_t h3 = std::hash<int>()(k.blur_radius_10x) ^ (std::hash<int>()(k.spread_10x) << 1);
            std::size_t h4 = std::hash<uint32_t>()(k.color_u32);
            return h1 ^ (h2 << 2) ^ (h3 << 3) ^ (h4 << 4);
        }
    };

    struct CachedShadow {
        ShadowKey key;
        BLImage image;
        int pad_x = 0;
        int pad_y = 0;
    };

    std::list<CachedShadow> lru_list_;
    std::unordered_map<ShadowKey, std::list<CachedShadow>::iterator, ShadowKeyHash> cache_map_;
    const size_t max_cache_entries_ = 128;
    std::mutex mutex_;
};

} // namespace tkblend
