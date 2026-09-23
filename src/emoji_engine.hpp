#pragma once

#include <blend2d.h>
#include <string>
#include <unordered_map>
#include <mutex>
#include <cstdint>

namespace tkblend {

// Emoji Engine powered by FreeType for color emoji rendering & font fallback
class EmojiEngine {
public:
    static EmojiEngine& instance();

    bool init();
    void set_emoji_font(const std::string& path);
    std::string get_emoji_font_path();

    static bool is_emoji(uint32_t codepoint);
    bool get_emoji_glyph(uint32_t codepoint, float target_size, BLImage& out_img, double& out_advance_x, double& out_bearing_y);

private:
    EmojiEngine();
    ~EmojiEngine();

    std::string resolve_system_emoji_font();

    struct GlyphKey {
        uint32_t codepoint;
        int size_int;

        bool operator==(const GlyphKey& o) const {
            return codepoint == o.codepoint && size_int == o.size_int;
        }
    };

    struct GlyphKeyHash {
        std::size_t operator()(const GlyphKey& k) const {
            return std::hash<uint32_t>()(k.codepoint) ^ (std::hash<int>()(k.size_int) << 16);
        }
    };

    struct CachedGlyph {
        BLImage image;
        double advance_x;
        double bearing_y;
        bool valid;
    };

    void* ft_lib_{nullptr};
    void* ft_face_{nullptr};
    std::string emoji_font_path_;
    std::unordered_map<GlyphKey, CachedGlyph, GlyphKeyHash> cache_;
    std::mutex mutex_;
    bool initialized_{false};
};

} // namespace tkblend
