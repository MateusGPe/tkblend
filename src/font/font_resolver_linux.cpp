#include "font_resolver.hpp"

#if defined(__linux__) || defined(__unix__) || defined(__FreeBSD__)
#include <fontconfig/fontconfig.h>
#include <filesystem>
#include <algorithm>
#include <vector>
#include <mutex>

namespace fs = std::filesystem;

namespace tkblend {

namespace {

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

    std::string resolve(const std::string& family) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default") {
            lower = "sans-serif";
        }

        std::lock_guard<std::mutex> lock(mutex_);
        if (!initialized_) {
            config_ = FcInitLoadConfigAndFonts();
            initialized_ = (config_ != nullptr);
        }
        if (!initialized_) {
            return fallback_scan(lower);
        }

        bool is_generic = (lower == "sans-serif" || lower == "serif" ||
                           lower == "monospace" || lower == "cursive" ||
                           lower == "fantasy" || lower == "system-ui" ||
                           lower == "emoji");

        if (is_generic) {
            std::string match = resolve_generic(lower);
            if (!match.empty()) return match;
        } else {
            std::string match = resolve_specific(family);
            if (!match.empty()) return match;
            // Also try with lower case family if different
            if (family != lower) {
                match = resolve_specific(lower);
                if (!match.empty()) return match;
            }
        }

        return fallback_scan(lower);
    }

private:
    std::mutex mutex_;
    FcConfig* config_ = nullptr;
    bool initialized_ = false;

    LinuxFontconfigManager() = default;
    ~LinuxFontconfigManager() = default;

    std::string resolve_generic(const std::string& generic_name) {
        FcPattern* pat = FcNameParse(reinterpret_cast<const FcChar8*>(generic_name.c_str()));
        if (!pat) return "";

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
    }

    std::string resolve_specific(const std::string& family_name) {
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
                            int slant = FC_SLANT_ROMAN;
                            FcPatternGetInteger(font_pat, FC_SLANT, 0, &slant);
                            FcChar8* style = nullptr;
                            FcPatternGetString(font_pat, FC_STYLE, 0, &style);
                            std::string style_str = style ? reinterpret_cast<const char*>(style) : "";
                            std::transform(style_str.begin(), style_str.end(), style_str.begin(), ::tolower);

                            if (slant == FC_SLANT_ROMAN && (style_str.empty() || style_str == "regular" || style_str == "book")) {
                                resolved_path = p;
                                break;
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
    }

    std::string fallback_scan(const std::string& family) {
        if (family == "sans-serif" || family == "default") {
            for (const auto& path : get_linux_font_candidates()) {
                try {
                    if (fs::exists(path)) return path;
                } catch (...) {}
            }
        }
        return "";
    }
};

} // namespace

std::string resolve_native_font_path(const std::string& family) {
    return LinuxFontconfigManager::instance().resolve(family);
}

} // namespace tkblend

#endif // Linux / Unix
