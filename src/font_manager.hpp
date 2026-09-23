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
    std::string find_system_font(const std::string& family, int weight = 400, bool italic = false);
    std::vector<std::string> get_loaded_fonts();
    std::vector<std::string> get_system_fonts(bool refresh = false);
    int register_font_directory(const std::string& dir_path);

    std::string get_active_font() const;
    bool set_active_font(const std::string& family_or_path);

    BLFontFace* get_font_face(const std::string& family, int weight = 400, bool italic = false);
    BLFont create_font(const std::string& family, float size, int weight = 400, bool italic = false);

private:
    FontManager();
    std::string resolve_system_font_path(const std::string& family, int weight = 400, bool italic = false);

    std::unordered_map<std::string, BLFontFace> font_faces_;
    std::unordered_map<std::string, std::string> font_paths_;
    std::vector<std::string> system_fonts_cache_;
    std::string default_font_family_;
    mutable std::mutex mutex_;
};

} // namespace tkblend
