#include "emoji_engine.hpp"
#include "font/font_resolver.hpp"

#include <ft2build.h>
#include FT_FREETYPE_H

#include <algorithm>
#include <filesystem>
#include <cstdlib>

namespace fs = std::filesystem;

namespace tkblend {

EmojiEngine& EmojiEngine::instance() {
    static EmojiEngine instance;
    return instance;
}

EmojiEngine::EmojiEngine() {
    emoji_font_path_ = resolve_system_emoji_font();
}

EmojiEngine::~EmojiEngine() {
    if (ft_face_) {
        FT_Done_Face(reinterpret_cast<FT_Face>(ft_face_));
        ft_face_ = nullptr;
    }
    if (ft_lib_) {
        FT_Done_FreeType(reinterpret_cast<FT_Library>(ft_lib_));
        ft_lib_ = nullptr;
    }
}

std::string EmojiEngine::resolve_system_emoji_font() {
#ifdef __linux__
    static const char* linux_paths[] = {
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf",
        "/usr/share/fonts/google-noto-color-emoji-fonts/NotoColorEmoji.ttf"
    };
    for (const char* p : linux_paths) {
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
    }
    const char* home = std::getenv("HOME");
    if (home) {
        std::string user_paths[] = {
            std::string(home) + "/.local/share/fonts/NotoColorEmoji.ttf",
            std::string(home) + "/.fonts/NotoColorEmoji.ttf"
        };
        for (const auto& up : user_paths) {
            try {
                if (fs::exists(up)) return up;
            } catch (...) {}
        }
    }
    std::string fc_emoji = resolve_native_font_path("emoji");
    if (!fc_emoji.empty()) {
        try {
            if (fs::exists(fc_emoji)) return fc_emoji;
        } catch (...) {}
    }
#elif defined(_WIN32)
    std::string win_dir = "C:\\Windows";
    if (const char* w = std::getenv("WINDIR")) win_dir = w;
    else if (const char* sr = std::getenv("SystemRoot")) win_dir = sr;
    std::string seg = win_dir + "\\Fonts\\seguiemj.ttf";
    try {
        if (fs::exists(seg)) return seg;
    } catch (...) {}
#elif defined(__APPLE__)
    static const char* mac_paths[] = {
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Core/Apple Color Emoji.ttc",
        "/Library/Fonts/Apple Color Emoji.ttc"
    };
    for (const char* p : mac_paths) {
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
    }
#endif
    return "";
}

bool EmojiEngine::init() {
    std::lock_guard<std::mutex> lock(mutex_);
    return init_locked();
}

bool EmojiEngine::init_locked() {
    if (initialized_) return (ft_face_ != nullptr);

    if (!ft_lib_) {
        FT_Library ft = nullptr;
        if (FT_Init_FreeType(&ft) != 0) {
            return false;
        }
        ft_lib_ = ft;
    }

    if (emoji_font_path_.empty()) {
        emoji_font_path_ = resolve_system_emoji_font();
    }
    if (emoji_font_path_.empty()) {
        return false;
    }
    try {
        if (!fs::exists(emoji_font_path_)) return false;
    } catch (...) {
        return false;
    }

    FT_Face face = nullptr;
    if (FT_New_Face(reinterpret_cast<FT_Library>(ft_lib_), emoji_font_path_.c_str(), 0, &face) != 0) {
        return false;
    }
    ft_face_ = face;

    if (face->num_fixed_sizes > 0) {
        FT_Select_Size(face, 0);
    }
    initialized_ = true;
    return true;
}

void EmojiEngine::set_emoji_font(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (path == emoji_font_path_) return;
    emoji_font_path_ = path;
    lru_list_.clear();
    cache_map_.clear();

    if (ft_face_) {
        FT_Done_Face(reinterpret_cast<FT_Face>(ft_face_));
        ft_face_ = nullptr;
    }
    if (ft_lib_) {
        FT_Done_FreeType(reinterpret_cast<FT_Library>(ft_lib_));
        ft_lib_ = nullptr;
    }
    initialized_ = false;
    init_locked();
}

std::string EmojiEngine::get_emoji_font_path() {
    std::lock_guard<std::mutex> lock(mutex_);
    return emoji_font_path_;
}

bool EmojiEngine::is_emoji(uint32_t cp) {
    if (cp >= 0x1F300 && cp <= 0x1FAFF) return true;
    if (cp >= 0x2600 && cp <= 0x27BF) return true;
    if (cp >= 0x2B00 && cp <= 0x2BFF) return true;
    if (cp >= 0x2300 && cp <= 0x23FF) return true;
    if (cp >= 0x1F1E6 && cp <= 0x1F1FF) return true;
    if (cp == 0xFE0E || cp == 0xFE0F || cp == 0x200D) return true;
    return false;
}

bool EmojiEngine::get_emoji_glyph(
    uint32_t codepoint,
    float target_size,
    BLImage& out_img,
    double& out_advance_x,
    double& out_bearing_y
) {
    int target_sz_int = static_cast<int>(target_size + 0.5f);
    if (target_sz_int < 1) target_sz_int = 1;

    GlyphKey key{codepoint, target_sz_int};

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = cache_map_.find(key);
    if (it != cache_map_.end()) {
        lru_list_.splice(lru_list_.begin(), lru_list_, it->second);
        if (!it->second->valid) return false;
        out_img = it->second->image;
        out_advance_x = it->second->advance_x;
        out_bearing_y = it->second->bearing_y;
        return true;
    }

    auto insert_cached_glyph = [&](const CachedGlyph& entry) {
        if (cache_map_.size() >= max_cache_entries_) {
            auto last = lru_list_.end();
            --last;
            cache_map_.erase(last->key);
            lru_list_.pop_back();
        }
        lru_list_.push_front(entry);
        cache_map_[key] = lru_list_.begin();
    };

    if (!init_locked()) {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    FT_Face face = reinterpret_cast<FT_Face>(ft_face_);
    if (!face) {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    FT_UInt glyph_index = FT_Get_Char_Index(face, codepoint);
    if (glyph_index == 0) {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    if (FT_Load_Glyph(face, glyph_index, FT_LOAD_COLOR) != 0) {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    FT_GlyphSlot slot = face->glyph;
    if (slot->format != FT_GLYPH_FORMAT_BITMAP) {
        if (FT_Render_Glyph(slot, FT_RENDER_MODE_NORMAL) != 0) {
            insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
            return false;
        }
    }

    FT_Bitmap& bmp = slot->bitmap;
    if (bmp.width == 0 || bmp.rows == 0 || !bmp.buffer) {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    int raw_w = bmp.width;
    int raw_h = bmp.rows;

    BLImage raw_bl_img;
    if (bmp.pixel_mode == FT_PIXEL_MODE_BGRA) {
        raw_bl_img.create_from_data(raw_w, raw_h, BL_FORMAT_PRGB32, bmp.buffer, bmp.pitch);
    } else if (bmp.pixel_mode == FT_PIXEL_MODE_GRAY) {
        raw_bl_img.create(raw_w, raw_h, BL_FORMAT_PRGB32);
        BLImageData img_data;
        if (raw_bl_img.make_mutable(&img_data) == BL_SUCCESS) {
            for (int r = 0; r < raw_h; ++r) {
                const uint8_t* src_row = bmp.buffer + r * bmp.pitch;
                uint32_t* dst_row = reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(img_data.pixel_data) + r * img_data.stride);
                for (int c = 0; c < raw_w; ++c) {
                    uint32_t a = src_row[c];
                    dst_row[c] = (a << 24) | (a << 16) | (a << 8) | a;
                }
            }
        }
    } else {
        insert_cached_glyph(CachedGlyph{key, BLImage(), 0, 0, false});
        return false;
    }

    double aspect = static_cast<double>(raw_w) / static_cast<double>(raw_h);
    int dest_h = target_sz_int;
    int dest_w = static_cast<int>(dest_h * aspect + 0.5);
    if (dest_w < 1) dest_w = 1;

    BLImage scaled_img;
    scaled_img.create(dest_w, dest_h, BL_FORMAT_PRGB32);
    {
        BLContext sctx(scaled_img);
        sctx.clear_all();
        double sx = static_cast<double>(dest_w) / static_cast<double>(raw_w);
        double sy = static_cast<double>(dest_h) / static_cast<double>(raw_h);
        sctx.scale(sx, sy);
        sctx.blit_image(BLPoint(0, 0), raw_bl_img);
        sctx.end();
    }

    double adv_x = dest_w * 1.15;
    double bear_y = dest_h * 0.82;

    CachedGlyph entry{key, scaled_img, adv_x, bear_y, true};
    insert_cached_glyph(entry);

    out_img = scaled_img;
    out_advance_x = adv_x;
    out_bearing_y = bear_y;
    return true;
}

void EmojiEngine::clear_cache() {
    std::lock_guard<std::mutex> lock(mutex_);
    cache_map_.clear();
    lru_list_.clear();
}

} // namespace tkblend
