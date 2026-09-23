#include "font_resolver.hpp"

#if defined(__APPLE__)
#include <CoreFoundation/CoreFoundation.h>
#include <CoreText/CoreText.h>
#include <filesystem>
#include <algorithm>
#include <vector>
#include <string>
#include <cstring>
#include <sys/syslimits.h>

namespace fs = std::filesystem;

namespace tkblend {

namespace {

const std::vector<std::string>& get_macos_candidate_fonts() {
    static std::vector<std::string> candidates = []() {
        std::vector<std::string> list;
        if (const char* home = std::getenv("HOME")) {
            list.push_back(std::string(home) + "/Library/Fonts/SFProText-Regular.otf");
            list.push_back(std::string(home) + "/Library/Fonts/Arial.ttf");
        }
        list.push_back("/System/Library/Fonts/SFProText-Regular.otf");
        list.push_back("/System/Library/Fonts/SFNS.ttf");
        list.push_back("/System/Library/Fonts/Helvetica.ttc");
        list.push_back("/Library/Fonts/Arial.ttf");
        list.push_back("/Library/Fonts/Helvetica.ttc");
        list.push_back("/System/Library/Fonts/Geneva.ttf");
        return list;
    }();
    return candidates;
}

class MacOSCoreTextResolver {
public:
    static MacOSCoreTextResolver& instance() {
        static MacOSCoreTextResolver inst;
        return inst;
    }

    std::string resolve(const std::string& family) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default" || lower == "sans-serif") {
            std::string match = resolve_coretext("Helvetica");
            if (!match.empty()) return match;
            match = resolve_coretext("Arial");
            if (!match.empty()) return match;
            return fallback_scan();
        } else if (lower == "serif") {
            std::string match = resolve_coretext("Times");
            if (!match.empty()) return match;
            match = resolve_coretext("Times New Roman");
            if (!match.empty()) return match;
        } else if (lower == "monospace") {
            std::string match = resolve_coretext("Menlo");
            if (!match.empty()) return match;
            match = resolve_coretext("Courier New");
            if (!match.empty()) return match;
        }

        std::string path = resolve_coretext(family);
        if (!path.empty()) return path;

        return fallback_scan();
    }

private:
    MacOSCoreTextResolver() = default;

    std::string resolve_coretext(const std::string& family_name) {
        CFStringRef cf_name = CFStringCreateWithCString(
            kCFAllocatorDefault,
            family_name.c_str(),
            kCFStringEncodingUTF8
        );
        if (!cf_name) return "";

        CTFontDescriptorRef descriptor = CTFontDescriptorCreateWithNameAndSize(cf_name, 0.0);
        CFRelease(cf_name);
        if (!descriptor) return "";

        CFURLRef url = (CFURLRef)CTFontDescriptorCopyAttribute(descriptor, kCTFontURLAttribute);
        CFRelease(descriptor);
        if (!url) return "";

        char buffer[PATH_MAX] = {0};
        Boolean ok = CFURLGetFileSystemRepresentation(url, true, (UInt8*)buffer, sizeof(buffer));
        CFRelease(url);

        if (ok && buffer[0] != '\0') {
            std::string path(buffer);
            try {
                if (fs::exists(path)) {
                    return path;
                }
            } catch (...) {}
        }

        return "";
    }

    std::string fallback_scan() {
        for (const auto& candidate : get_macos_candidate_fonts()) {
            try {
                if (fs::exists(candidate)) return candidate;
            } catch (...) {}
        }
        return "";
    }
};

} // namespace

std::string resolve_native_font_path(const std::string& family) {
    return MacOSCoreTextResolver::instance().resolve(family);
}

} // namespace tkblend

#endif // __APPLE__
