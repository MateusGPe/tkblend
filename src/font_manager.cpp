#include "font_manager.hpp"
#include "font/font_resolver.hpp"
#include "font/embedded_fonts.hpp"

#include <algorithm>
#include <filesystem>
#include <stdexcept>
#include <iostream>

namespace fs = std::filesystem;

namespace tkblend {

FontManager& FontManager::instance() {
    static FontManager instance;
    return instance;
}

FontManager::FontManager() {
    // Fully lazy on-demand initialization. Zero blocking I/O at startup.
}

std::string FontManager::resolve_system_font_path(const std::string& family, int weight, bool italic) {
    std::string lower_family = family;
    std::transform(lower_family.begin(), lower_family.end(), lower_family.begin(), ::tolower);

    if (lower_family.empty() || lower_family == "default") {
        lower_family = default_font_family_.empty() ? "sans-serif" : default_font_family_;
    }

    std::string cache_key = lower_family;
    if (weight != 400 || italic) {
        cache_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
    }

    // 1. Check cached paths
    auto it = font_paths_.find(cache_key);
    if (it != font_paths_.end()) {
        try {
            if (fs::exists(it->second)) {
                return it->second;
            }
        } catch (const std::exception& e) {
            throw std::runtime_error(
                std::string("FontManager::resolve_system_font_path: filesystem error checking cached path '")
                + it->second + "': " + e.what());
        }
    }

    // 2. Query native platform resolver (DirectWrite/GDI on Win, CoreText on macOS, Fontconfig on Linux)
    std::string native_path = resolve_native_font_path(family, weight, italic);
    if (native_path.empty() && lower_family != family) {
        native_path = resolve_native_font_path(lower_family, weight, italic);
    }

    if (!native_path.empty()) {
        try {
            if (fs::exists(native_path)) {
                font_paths_[cache_key] = native_path;
                return native_path;
            }
        } catch (const std::exception& e) {
            throw std::runtime_error(
                std::string("FontManager::resolve_system_font_path: filesystem error checking native path '")
                + native_path + "': " + e.what());
        }
    }

    return "";
}

bool FontManager::load_font_face(const std::string& name, const std::string& filepath) {
    try {
        if (!fs::exists(filepath)) {
            return false;
        }
    } catch (const std::exception& e) {
        throw std::runtime_error(
            std::string("FontManager::load_font_face: filesystem error checking path '")
            + filepath + "': " + e.what());
    }

    std::lock_guard<std::mutex> lock(mutex_);
    BLFontFace face;
    BLResult result = face.create_from_file(filepath.c_str());
    if (result == BL_SUCCESS) {
        std::string lower_name = name;
        std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
        font_faces_[lower_name] = face;
        font_paths_[lower_name] = filepath;

        // Register canonical family name from OpenType metadata
        const BLString& fam = face.family_name();
        if (!fam.is_empty()) {
            std::string real_fam = fam.data();
            std::string lower_real = real_fam;
            std::transform(lower_real.begin(), lower_real.end(), lower_real.begin(), ::tolower);
            if (lower_real != lower_name) {
                font_faces_[lower_real] = face;
                font_paths_[lower_real] = filepath;
            }
        }

        if (default_font_family_.empty() || lower_name == "sans-serif" || lower_name == "default") {
            default_font_family_ = lower_name;
        }
        return true;
    }
    return false;
}

bool FontManager::load_font_face_from_data(const std::string& name, const void* data, size_t size) {
    if (!data || size == 0) return false;

    std::lock_guard<std::mutex> lock(mutex_);

    // Copy font buffer to keep it alive
    std::vector<uint8_t> buf(static_cast<const uint8_t*>(data), static_cast<const uint8_t*>(data) + size);
    font_memory_buffers_.push_back(std::move(buf));
    const auto& stored_buf = font_memory_buffers_.back();

    BLFontData font_data;
    BLResult res = font_data.create_from_data(stored_buf.data(), stored_buf.size());
    if (res != BL_SUCCESS) {
        return false;
    }
    font_datas_.push_back(font_data);

    BLFontFace face;
    res = face.create_from_data(font_data, 0);
    if (res == BL_SUCCESS) {
        std::string lower_name = name;
        std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
        font_faces_[lower_name] = face;

        const BLString& fam = face.family_name();
        if (!fam.is_empty()) {
            std::string real_fam = fam.data();
            std::string lower_real = real_fam;
            std::transform(lower_real.begin(), lower_real.end(), lower_real.begin(), ::tolower);
            if (lower_real != lower_name) {
                font_faces_[lower_real] = face;
            }
        }
        return true;
    }
    return false;
}

void FontManager::_ensure_embedded_fonts_loaded_locked() {
    if (embedded_loaded_) return;
    embedded_loaded_ = true;

    const auto& embedded = get_embedded_fonts();
    for (const auto& ef : embedded) {
        std::vector<uint8_t> decompressed;
        if (decompress_embedded_font(ef, decompressed)) {
            font_memory_buffers_.push_back(std::move(decompressed));
            const auto& stored_buf = font_memory_buffers_.back();

            BLFontData font_data;
            if (font_data.create_from_data(stored_buf.data(), stored_buf.size()) == BL_SUCCESS) {
                font_datas_.push_back(font_data);
                BLFontFace face;
                if (face.create_from_data(font_data, 0) == BL_SUCCESS) {
                    std::string lower_alias = ef.name;
                    std::transform(lower_alias.begin(), lower_alias.end(), lower_alias.begin(), ::tolower);
                    font_faces_[lower_alias] = face;

                    std::string lower_fam = ef.family;
                    std::transform(lower_fam.begin(), lower_fam.end(), lower_fam.begin(), ::tolower);
                    if (lower_fam != lower_alias) {
                        font_faces_[lower_fam] = face;
                    }

                    fallback_families_.push_back(lower_alias);
                }
            }
        }
    }
}

void FontManager::ensure_embedded_fonts_loaded() {
    std::lock_guard<std::mutex> lock(mutex_);
    _ensure_embedded_fonts_loaded_locked();
}

bool FontManager::font_has_glyph(const BLFont& font, uint32_t codepoint) {
    if (font.is_empty() || codepoint == 0) return false;
    BLGlyphBuffer gb;
    gb.set_text(&codepoint, 1, BL_TEXT_ENCODING_UTF32);
    BLGlyphMappingState state;
    font.map_text_to_glyphs(gb, state);
    if (state.undefined_count == 0 && gb.size() > 0) {
        const uint32_t* glyphs = gb.content();
        return glyphs && glyphs[0] != 0;
    }
    return false;
}

BLFontFace* FontManager::_find_fallback_face_for_codepoint_locked(uint32_t codepoint, int weight, bool italic) {
    _ensure_embedded_fonts_loaded_locked();

    // 1. Check embedded icon fonts and active fallback families first
    for (const auto& fam : fallback_families_) {
        auto it = font_faces_.find(fam);
        if (it != font_faces_.end() && it->second.is_valid()) {
            BLFont test_font;
            test_font.create_from_face(it->second, 12.0f);
            if (font_has_glyph(test_font, codepoint)) {
                return &it->second;
            }
        }
    }

    // 2. Check standard system fallback fonts
    static const std::vector<std::string> sys_fallbacks = {
        "Segoe UI Symbol", "Segoe UI Emoji", "Arial Unicode MS",
        "Apple Symbols", "Apple Color Emoji",
        "Noto Sans", "Noto Sans Symbols", "Noto Color Emoji",
        "DejaVu Sans", "Symbola", "FreeSans", "Unifont"
    };

    for (const auto& fam : sys_fallbacks) {
        BLFontFace* face = _get_font_face_locked(fam, weight, italic);
        if (face && face->is_valid()) {
            BLFont test_font;
            test_font.create_from_face(*face, 12.0f);
            if (font_has_glyph(test_font, codepoint)) {
                return face;
            }
        }
    }

    return nullptr;
}

BLFont FontManager::create_fallback_font_for_codepoint(uint32_t codepoint, float size, int weight, bool italic) {
    std::lock_guard<std::mutex> lock(mutex_);
    BLFontFace* face = _find_fallback_face_for_codepoint_locked(codepoint, weight, italic);
    BLFont font;
    if (face && face->is_valid()) {
        font.create_from_face(*face, size);
    }
    return font;
}

std::string FontManager::find_system_font(const std::string& family, int weight, bool italic) {
    std::lock_guard<std::mutex> lock(mutex_);
    return resolve_system_font_path(family, weight, italic);
}

std::vector<std::string> FontManager::get_loaded_fonts() {
    std::lock_guard<std::mutex> lock(mutex_);
    _ensure_embedded_fonts_loaded_locked();
    std::vector<std::string> fonts;
    fonts.reserve(font_faces_.size());
    for (const auto& kv : font_faces_) {
        fonts.push_back(kv.first);
    }
    std::sort(fonts.begin(), fonts.end());
    return fonts;
}

std::vector<std::string> FontManager::get_system_fonts(bool refresh) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!system_fonts_cache_.empty() && !refresh) {
        return system_fonts_cache_;
    }
    system_fonts_cache_ = get_native_system_fonts();
    std::sort(system_fonts_cache_.begin(), system_fonts_cache_.end());
    return system_fonts_cache_;
}

int FontManager::register_font_directory(const std::string& dir_path) {
    int count = 0;
    try {
        if (!fs::exists(dir_path)) return 0;
        for (const auto& entry : fs::recursive_directory_iterator(
                 dir_path, fs::directory_options::skip_permission_denied)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                if (ext == ".ttf" || ext == ".otf" || ext == ".ttc") {
                    std::string stem = entry.path().stem().string();
                    std::string p = entry.path().string();
                    // A single bad font file must not abort the entire directory scan.
                    try {
                        if (load_font_face(stem, p)) {
                            count++;
                        }
                    } catch (const std::exception& /*e*/) {
                        // Skip unreadable / corrupt font files silently.
                    }
                }
            }
        }
    } catch (const std::exception& e) {
        throw std::runtime_error(
            std::string("FontManager::register_font_directory: error scanning '")
            + dir_path + "': " + e.what());
    }
    return count;
}

std::string FontManager::get_active_font() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (default_font_family_.empty()) {
        return "sans-serif";
    }
    return default_font_family_;
}

bool FontManager::set_active_font(const std::string& family_or_path) {
    if (family_or_path.empty()) return false;
    std::string lower = family_or_path;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    // If it looks like a file path, try loading it first (outside the main lock).
    bool looks_like_path = false;
    try {
        looks_like_path = fs::exists(family_or_path) && fs::is_regular_file(family_or_path);
    } catch (const std::exception& e) {
        throw std::runtime_error(
            std::string("FontManager::set_active_font: filesystem error checking path '")
            + family_or_path + "': " + e.what());
    }

    if (looks_like_path) {
        std::string stem = fs::path(family_or_path).stem().string();
        if (load_font_face(stem, family_or_path)) {
            std::lock_guard<std::mutex> lock(mutex_);
            default_font_family_ = stem;
            return true;
        }
    }

    std::lock_guard<std::mutex> lock(mutex_);
    // Check if already loaded
    if (font_faces_.find(lower) != font_faces_.end()) {
        default_font_family_ = lower;
        return true;
    }

    // Check if resolvable on system
    std::string resolved = resolve_system_font_path(lower, 400, false);
    if (!resolved.empty()) {
        default_font_family_ = lower;
        return true;
    }
    return false;
}

// Private — MUST be called with mutex_ already held.
// Returns a pointer into font_faces_; valid only while the lock is held.
BLFontFace* FontManager::_get_font_face_locked(const std::string& family, int weight, bool italic) {
    _ensure_embedded_fonts_loaded_locked();

    std::string lower_family = family;
    std::transform(lower_family.begin(), lower_family.end(), lower_family.begin(), ::tolower);

    if (lower_family.empty() || lower_family == "default") {
        lower_family = default_font_family_.empty() ? "sans-serif" : default_font_family_;
    }

    std::string cache_key = lower_family;
    if (weight != 400 || italic) {
        cache_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
    }

    // 1. Check already loaded face
    auto it = font_faces_.find(cache_key);
    if (it != font_faces_.end()) {
        return &it->second;
    }

    // 2. Lazily resolve path (resolve_system_font_path reads font_paths_ but does not
    //    lock — caller already holds mutex_).
    std::string path = resolve_system_font_path(lower_family, weight, italic);
    if (!path.empty()) {
        BLFontFace face;
        if (face.create_from_file(path.c_str()) == BL_SUCCESS) {
            auto inserted = font_faces_.emplace(cache_key, face);
            font_paths_[cache_key] = path;

            const BLString& fam = face.family_name();
            if (!fam.is_empty()) {
                std::string real_fam = fam.data();
                std::string lower_real = real_fam;
                std::transform(lower_real.begin(), lower_real.end(), lower_real.begin(), ::tolower);
                if (lower_real != lower_family) {
                    std::string real_key = lower_real;
                    if (weight != 400 || italic) {
                        real_key += "#" + std::to_string(weight) + (italic ? "i" : "r");
                    }
                    font_faces_.emplace(real_key, face);
                    font_paths_[real_key] = path;
                }
            }

            if (default_font_family_.empty()) {
                default_font_family_ = lower_family;
            }
            return &inserted.first->second;
        }
    }

    // 3. Fallback to base family without weight/italic if not found
    if (cache_key != lower_family) {
        auto base_it = font_faces_.find(lower_family);
        if (base_it != font_faces_.end()) {
            return &base_it->second;
        }
    }

    // 4. Fallback to sans-serif
    if (lower_family != "sans-serif") {
        auto sans_it = font_faces_.find("sans-serif");
        if (sans_it != font_faces_.end()) {
            return &sans_it->second;
        }

        std::string default_path = resolve_system_font_path("sans-serif", weight, italic);
        if (default_path.empty()) {
            default_path = resolve_system_font_path("sans-serif", 400, false);
        }
        if (!default_path.empty()) {
            BLFontFace face;
            if (face.create_from_file(default_path.c_str()) == BL_SUCCESS) {
                auto inserted = font_faces_.emplace("sans-serif", face);
                font_paths_["sans-serif"] = default_path;
                if (default_font_family_.empty()) {
                    default_font_family_ = "sans-serif";
                }
                return &inserted.first->second;
            }
        }
    }

    // 5. Any available font face
    if (!font_faces_.empty()) {
        return &font_faces_.begin()->second;
    }

    return nullptr;
}

BLFont FontManager::create_font(const std::string& family, float size, int weight, bool italic) {
    // Hold the lock for the entire resolution + font construction so the raw BLFontFace*
    // returned by _get_font_face_locked() never escapes the critical section.
    std::lock_guard<std::mutex> lock(mutex_);
    BLFontFace* face = _get_font_face_locked(family, weight, italic);
    BLFont font;
    if (face && face->is_valid()) {
        font.create_from_face(*face, size);
    }
    return font;
}

void FontManager::clear_cache() {
    std::lock_guard<std::mutex> lock(mutex_);
    font_faces_.clear();
    font_paths_.clear();
    font_datas_.clear();
    font_memory_buffers_.clear();
    fallback_families_.clear();
    system_fonts_cache_.clear();
    embedded_loaded_ = false;
}

} // namespace tkblend
