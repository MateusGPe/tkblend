#include "font_resolver.hpp"

#if defined(__linux__) || defined(__unix__) || defined(__FreeBSD__)
#include <filesystem>
#include <algorithm>
#include <vector>
#include <set>
#include <mutex>
#include <cmath>
#include <cstdlib>

#if defined(TKBLEND_HAS_FONTCONFIG)
#include <fontconfig/fontconfig.h>
#else
#include <dlfcn.h>
typedef void FcConfig;
typedef void FcPattern;
typedef void FcFontSet;
typedef void FcObjectSet;
typedef unsigned char FcChar8;
typedef int FcResult;
typedef int FcMatchKind;

#define FC_FAMILY "family"
#define FC_STYLE "style"
#define FC_SLANT "slant"
#define FC_WEIGHT "weight"
#define FC_FILE "file"

#define FcResultMatch 0
#define FcResultNoMatch 1
#define FcMatchPattern 0

#define FC_SLANT_ROMAN 0
#define FC_SLANT_ITALIC 100
#define FC_SLANT_OBLIQUE 110

#define FC_WEIGHT_THIN 0
#define FC_WEIGHT_EXTRALIGHT 40
#define FC_WEIGHT_LIGHT 50
#define FC_WEIGHT_REGULAR 80
#define FC_WEIGHT_MEDIUM 100
#define FC_WEIGHT_DEMIBOLD 180
#define FC_WEIGHT_BOLD 200
#define FC_WEIGHT_EXTRABOLD 205
#define FC_WEIGHT_BLACK 210

struct _FcFontSet {
    int nfont;
    int sfont;
    FcPattern** fonts;
};
#endif

namespace fs = std::filesystem;

namespace tkblend {

namespace {

int map_weight_to_fc(int weight) {
    if (weight <= 150) return 0;    // Thin
    if (weight <= 250) return 40;   // Extra Light
    if (weight <= 350) return 50;   // Light
    if (weight <= 450) return 80;   // Regular / Normal
    if (weight <= 550) return 100;  // Medium
    if (weight <= 650) return 180;  // Semi Bold
    if (weight <= 750) return 200;  // Bold
    if (weight <= 850) return 205;  // Extra Bold
    return 210;                     // Black
}

const std::vector<std::string>& get_linux_font_candidates() {
    static std::vector<std::string> candidates = []() {
        std::vector<std::string> list;
        if (const char* xdg = std::getenv("XDG_DATA_HOME")) {
            list.push_back(std::string(xdg) + "/fonts/dejavu/DejaVuSans.ttf");
            list.push_back(std::string(xdg) + "/fonts/truetype/dejavu/DejaVuSans.ttf");
        } else if (const char* home = std::getenv("HOME")) {
            list.push_back(std::string(home) + "/.local/share/fonts/dejavu/DejaVuSans.ttf");
            list.push_back(std::string(home) + "/.fonts/DejaVuSans.ttf");
        }
        list.push_back("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf");
        list.push_back("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf");
        list.push_back("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf");
        list.push_back("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf");
        list.push_back("/usr/share/fonts/truetype/roboto/unhinted/Roboto-Regular.ttf");
        list.push_back("/usr/share/fonts/TTF/DejaVuSans.ttf");
        list.push_back("/usr/share/fonts/noto/NotoSans-Regular.ttf");
        list.push_back("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf");
        return list;
    }();
    return candidates;
}

class LinuxFontconfigManager {
public:
    static LinuxFontconfigManager& instance() {
        static LinuxFontconfigManager mgr;
        return mgr;
    }

    std::string resolve(const std::string& family, int weight, bool italic) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default") {
            lower = "sans-serif";
        }

        std::lock_guard<std::mutex> lock(mutex_);
        ensure_initialized();

        if (!initialized_) {
            return fallback_scan(family, weight, italic);
        }

        bool is_generic = (lower == "sans-serif" || lower == "serif" ||
                           lower == "monospace" || lower == "cursive" ||
                           lower == "fantasy" || lower == "system-ui" ||
                           lower == "emoji");

        if (is_generic) {
            std::string match = resolve_generic(lower, weight, italic);
            if (!match.empty()) return match;
        } else {
            std::string match = resolve_specific(family, weight, italic);
            if (!match.empty()) return match;
            if (family != lower) {
                match = resolve_specific(lower, weight, italic);
                if (!match.empty()) return match;
            }
        }

        return fallback_scan(family, weight, italic);
    }

    std::vector<std::string> get_system_fonts() {
        std::lock_guard<std::mutex> lock(mutex_);
        ensure_initialized();

        std::set<std::string> unique_families;
#if defined(TKBLEND_HAS_FONTCONFIG)
        if (initialized_ && config_) {
            FcPattern* pat = FcPatternCreate();
            FcObjectSet* os = FcObjectSetBuild(FC_FAMILY, nullptr);
            if (pat && os) {
                FcFontSet* fs_list = FcFontList(config_, pat, os);
                if (fs_list) {
                    for (int i = 0; i < fs_list->nfont; ++i) {
                        FcChar8* fam = nullptr;
                        int val_idx = 0;
                        while (FcPatternGetString(fs_list->fonts[i], FC_FAMILY, val_idx++, &fam) == FcResultMatch && fam) {
                            unique_families.insert(reinterpret_cast<const char*>(fam));
                        }
                    }
                    FcFontSetDestroy(fs_list);
                }
                FcObjectSetDestroy(os);
                FcPatternDestroy(pat);
            }
        }
#endif

        if (unique_families.empty()) {
            // Fallback directory scan for family names
            const char* base_dirs[] = { "/usr/share/fonts", "/usr/local/share/fonts" };
            for (const char* d : base_dirs) {
                try {
                    if (fs::exists(d)) {
                        for (const auto& entry : fs::recursive_directory_iterator(d, fs::directory_options::skip_permission_denied)) {
                            if (entry.is_regular_file()) {
                                std::string ext = entry.path().extension().string();
                                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                                if (ext == ".ttf" || ext == ".otf" || ext == ".ttc") {
                                    unique_families.insert(entry.path().stem().string());
                                }
                            }
                        }
                    }
                } catch (...) {}
            }
        }

        std::vector<std::string> result(unique_families.begin(), unique_families.end());
        return result;
    }

private:
    std::mutex mutex_;
#if defined(TKBLEND_HAS_FONTCONFIG)
    FcConfig* config_ = nullptr;
#else
    void* config_ = nullptr;
    void* dl_handle_ = nullptr;
#endif
    bool initialized_ = false;
    bool init_attempted_ = false;

    LinuxFontconfigManager() = default;
    ~LinuxFontconfigManager() {
#if !defined(TKBLEND_HAS_FONTCONFIG)
        if (dl_handle_) {
            dlclose(dl_handle_);
            dl_handle_ = nullptr;
        }
#endif
    }

    void ensure_initialized() {
        if (init_attempted_) return;
        init_attempted_ = true;

#if defined(TKBLEND_HAS_FONTCONFIG)
        config_ = FcInitLoadConfigAndFonts();
        initialized_ = (config_ != nullptr);
#else
        dl_handle_ = dlopen("libfontconfig.so.1", RTLD_LAZY | RTLD_LOCAL);
        if (!dl_handle_) {
            dl_handle_ = dlopen("libfontconfig.so", RTLD_LAZY | RTLD_LOCAL);
        }
        if (dl_handle_) {
            auto init_fn = (void* (*)())dlsym(dl_handle_, "FcInitLoadConfigAndFonts");
            if (init_fn) {
                config_ = init_fn();
                initialized_ = (config_ != nullptr);
            }
        }
#endif
    }

    std::string resolve_generic(const std::string& generic_name, int weight, bool italic) {
#if defined(TKBLEND_HAS_FONTCONFIG)
        if (!config_) return "";
        FcPattern* pat = FcNameParse(reinterpret_cast<const FcChar8*>(generic_name.c_str()));
        if (!pat) return "";

        int fc_weight = map_weight_to_fc(weight);
        int fc_slant = italic ? FC_SLANT_ITALIC : FC_SLANT_ROMAN;
        FcPatternAddInteger(pat, FC_WEIGHT, fc_weight);
        FcPatternAddInteger(pat, FC_SLANT, fc_slant);

        FcConfigSubstitute(config_, pat, FcMatchPattern);
        FcDefaultSubstitute(pat);

        FcResult result = FcResultNoMatch;
        FcPattern* match = FcFontMatch(config_, pat, &result);
        std::string resolved_path;

        if (match) {
            FcChar8* file = nullptr;
            if (FcPatternGetString(match, FC_FILE, 0, &file) == FcResultMatch && file) {
                std::string p = reinterpret_cast<const char*>(file);
                try {
                    if (fs::exists(p)) {
                        resolved_path = p;
                    }
                } catch (...) {}
            }
            FcPatternDestroy(match);
        }
        FcPatternDestroy(pat);
        return resolved_path;
#else
        (void)generic_name; (void)weight; (void)italic;
        return "";
#endif
    }

    std::string resolve_specific(const std::string& family_name, int weight, bool italic) {
#if defined(TKBLEND_HAS_FONTCONFIG)
        if (!config_) return "";
        FcPattern* pat = FcPatternCreate();
        if (!pat) return "";

        FcPatternAddString(pat, FC_FAMILY, reinterpret_cast<const FcChar8*>(family_name.c_str()));

        FcObjectSet* os = FcObjectSetBuild(FC_FILE, FC_FAMILY, FC_STYLE, FC_SLANT, FC_WEIGHT, nullptr);
        if (!os) {
            FcPatternDestroy(pat);
            return "";
        }

        FcFontSet* fs_list = FcFontList(config_, pat, os);
        std::string resolved_path;
        std::string fallback_candidate;
        int target_weight = map_weight_to_fc(weight);
        int target_slant = italic ? FC_SLANT_ITALIC : FC_SLANT_ROMAN;
        int best_score = 999999;

        if (fs_list) {
            for (int i = 0; i < fs_list->nfont; ++i) {
                FcPattern* font_pat = fs_list->fonts[i];
                FcChar8* file = nullptr;
                if (FcPatternGetString(font_pat, FC_FILE, 0, &file) == FcResultMatch && file) {
                    std::string p = reinterpret_cast<const char*>(file);
                    try {
                        if (fs::exists(p)) {
                            if (fallback_candidate.empty()) {
                                fallback_candidate = p;
                            }

                            int font_slant = 0;
                            int font_weight = FC_WEIGHT_REGULAR;
                            FcPatternGetInteger(font_pat, FC_SLANT, 0, &font_slant);
                            FcPatternGetInteger(font_pat, FC_WEIGHT, 0, &font_weight);

                            int slant_penalty = (target_slant > 0) == (font_slant > 0) ? 0 : 500;
                            int weight_penalty = std::abs(font_weight - target_weight);
                            int score = slant_penalty + weight_penalty;

                            if (score < best_score) {
                                best_score = score;
                                resolved_path = p;
                            }
                        }
                    } catch (...) {}
                }
            }
            if (resolved_path.empty()) {
                resolved_path = fallback_candidate;
            }
            FcFontSetDestroy(fs_list);
        }

        FcObjectSetDestroy(os);
        FcPatternDestroy(pat);
        return resolved_path;
#else
        (void)family_name; (void)weight; (void)italic;
        return "";
#endif
    }

    std::string fallback_scan(const std::string& family, int weight, bool italic) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower == "sans-serif" || lower == "default") {
            for (const auto& path : get_linux_font_candidates()) {
                try {
                    if (fs::exists(path)) return path;
                } catch (...) {}
            }
        }

        // Search in system font directories for matching file stems
        const char* base_dirs[] = { "/usr/share/fonts", "/usr/local/share/fonts" };
        std::string fallback_candidate;
        for (const char* d : base_dirs) {
            try {
                if (fs::exists(d)) {
                    for (const auto& entry : fs::recursive_directory_iterator(d, fs::directory_options::skip_permission_denied)) {
                        if (entry.is_regular_file()) {
                            std::string stem = entry.path().stem().string();
                            std::string lower_stem = stem;
                            std::transform(lower_stem.begin(), lower_stem.end(), lower_stem.begin(), ::tolower);

                            if (lower_stem.find(lower) != std::string::npos) {
                                if (fallback_candidate.empty()) {
                                    fallback_candidate = entry.path().string();
                                }
                                bool is_bold = (lower_stem.find("bold") != std::string::npos || lower_stem.find("-b") != std::string::npos);
                                bool is_italic = (lower_stem.find("italic") != std::string::npos || lower_stem.find("oblique") != std::string::npos);

                                if (is_bold == (weight >= 600) && is_italic == italic) {
                                    return entry.path().string();
                                }
                            }
                        }
                    }
                }
            } catch (...) {}
        }

        return fallback_candidate;
    }
};

} // namespace

std::string resolve_native_font_path(const std::string& family, int weight, bool italic) {
    return LinuxFontconfigManager::instance().resolve(family, weight, italic);
}

std::vector<std::string> get_native_system_fonts() {
    return LinuxFontconfigManager::instance().get_system_fonts();
}

} // namespace tkblend

#endif // Linux / Unix
