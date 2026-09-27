#pragma once

#include <blend2d.h>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>

namespace tkblend {

// Font Manager with system font discovery & typography control
class FontManager {
public:
    static FontManager& instance();

    bool load_font_face(const std::string& name, const std::string& filepath);
    bool load_font_face_from_data(const std::string& name, const void* data, size_t size);
    std::string find_system_font(const std::string& family, int weight = 400, bool italic = false);
    std::vector<std::string> get_loaded_fonts();
    std::vector<std::string> get_system_fonts(bool refresh = false);
    int register_font_directory(const std::string& dir_path);

    std::string get_active_font() const;
    bool set_active_font(const std::string& family_or_path);
    void clear_cache();

    // Ensures embedded icon fonts (Font Awesome, Lucide) are loaded
    void ensure_embedded_fonts_loaded();

    // Check whether a font has a glyph for a specific codepoint
    static bool font_has_glyph(const BLFont& font, uint32_t codepoint);

    // Creates a font matching family and size
    BLFont create_font(const std::string& family, float size, int weight = 400, bool italic = false);

    // Creates a fallback font that can render the given codepoint
    BLFont create_fallback_font_for_codepoint(uint32_t codepoint, float size, int weight = 400, bool italic = false);

private:
    FontManager();
    std::string resolve_system_font_path(const std::string& family, int weight = 400, bool italic = false);

    // Must be called with mutex_ already held. Returns a raw pointer into font_faces_ that
    // is valid only while the lock is held — never store or use this pointer after releasing.
    BLFontFace* _get_font_face_locked(const std::string& family, int weight = 400, bool italic = false);
    BLFontFace* _find_fallback_face_for_codepoint_locked(uint32_t codepoint, int weight = 400, bool italic = false);
    void _ensure_embedded_fonts_loaded_locked();

    std::unordered_map<std::string, BLFontFace> font_faces_;
    std::unordered_map<std::string, std::string> font_paths_;
    std::vector<std::string> fallback_families_;
    std::vector<BLFontData> font_datas_;
    std::vector<std::vector<uint8_t>> font_memory_buffers_;
    std::vector<std::string> system_fonts_cache_;
    std::string default_font_family_;
    bool embedded_loaded_{false};
    mutable std::mutex mutex_;
};

} // namespace tkblend
