#include "font_resolver.hpp"

#if defined(__APPLE__)
#include <CoreFoundation/CoreFoundation.h>
#include <CoreText/CoreText.h>
#include <filesystem>
#include <algorithm>
#include <vector>
#include <set>
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

std::string cfstring_to_utf8(CFStringRef cf_str) {
    if (!cf_str) return "";
    char buf[512];
    if (CFStringGetCString(cf_str, buf, sizeof(buf), kCFStringEncodingUTF8)) {
        return std::string(buf);
    }
    return "";
}

class MacOSCoreTextResolver {
public:
    static MacOSCoreTextResolver& instance() {
        static MacOSCoreTextResolver inst;
        return inst;
    }

    std::string resolve(const std::string& family, int weight, bool italic) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default" || lower == "sans-serif") {
            std::string match = resolve_coretext("Helvetica", weight, italic);
            if (!match.empty()) return match;
            match = resolve_coretext("Arial", weight, italic);
            if (!match.empty()) return match;
            return fallback_scan();
        } else if (lower == "serif") {
            std::string match = resolve_coretext("Times", weight, italic);
            if (!match.empty()) return match;
            match = resolve_coretext("Times New Roman", weight, italic);
            if (!match.empty()) return match;
        } else if (lower == "monospace") {
            std::string match = resolve_coretext("Menlo", weight, italic);
            if (!match.empty()) return match;
            match = resolve_coretext("Courier New", weight, italic);
            if (!match.empty()) return match;
        }

        std::string path = resolve_coretext(family, weight, italic);
        if (!path.empty()) return path;

        return fallback_scan();
    }

    std::vector<std::string> get_system_fonts() {
        std::set<std::string> unique_families;
        CTFontCollectionRef collection = CTFontCollectionCreateFromAvailableFonts(nullptr);
        if (collection) {
            CFArrayRef descriptors = CTFontCollectionCreateMatchingFontDescriptors(collection);
            if (descriptors) {
                CFIndex count = CFArrayGetCount(descriptors);
                for (CFIndex i = 0; i < count; ++i) {
                    CTFontDescriptorRef desc = (CTFontDescriptorRef)CFArrayGetValueAtIndex(descriptors, i);
                    CFStringRef cf_fam = (CFStringRef)CTFontDescriptorCopyAttribute(desc, kCTFontFamilyNameAttribute);
                    if (cf_fam) {
                        std::string fam_str = cfstring_to_utf8(cf_fam);
                        if (!fam_str.empty()) unique_families.insert(fam_str);
                        CFRelease(cf_fam);
                    }
                }
                CFRelease(descriptors);
            }
            CFRelease(collection);
        }

        if (unique_families.empty()) {
            for (const auto& path : get_macos_candidate_fonts()) {
                try {
                    if (fs::exists(path)) {
                        unique_families.insert(fs::path(path).stem().string());
                    }
                } catch (...) {}
            }
        }

        return std::vector<std::string>(unique_families.begin(), unique_families.end());
    }

private:
    MacOSCoreTextResolver() = default;

    std::string resolve_coretext(const std::string& family_name, int weight, bool italic) {
        CFStringRef cf_name = CFStringCreateWithCString(
            kCFAllocatorDefault,
            family_name.c_str(),
            kCFStringEncodingUTF8
        );
        if (!cf_name) return "";

        CTFontDescriptorRef descriptor = nullptr;
        uint32_t traits = 0;
        if (weight >= 600) traits |= kCTFontTraitBold;
        if (italic) traits |= kCTFontTraitItalic;

        if (traits != 0) {
            CFNumberRef sym_traits = CFNumberCreate(kCFAllocatorDefault, kCFNumberSInt32Type, &traits);
            const void* trait_keys[] = { kCTFontSymbolicTrait };
            const void* trait_values[] = { sym_traits };
            CFDictionaryRef traits_dict = CFDictionaryCreate(
                kCFAllocatorDefault,
                trait_keys, trait_values, 1,
                &kCFTypeDictionaryKeyCallBacks,
                &kCFTypeDictionaryValueCallBacks
            );

            const void* attr_keys[] = { kCTFontFamilyNameAttribute, kCTFontTraitsAttribute };
            const void* attr_values[] = { cf_name, traits_dict };
            CFDictionaryRef attr_dict = CFDictionaryCreate(
                kCFAllocatorDefault,
                attr_keys, attr_values, 2,
                &kCFTypeDictionaryKeyCallBacks,
                &kCFTypeDictionaryValueCallBacks
            );

            descriptor = CTFontDescriptorCreateWithAttributes(attr_dict);
            CFRelease(attr_dict);
            CFRelease(traits_dict);
            CFRelease(sym_traits);
        } else {
            descriptor = CTFontDescriptorCreateWithNameAndSize(cf_name, 0.0);
        }

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

std::string resolve_native_font_path(const std::string& family, int weight, bool italic) {
    return MacOSCoreTextResolver::instance().resolve(family, weight, italic);
}

std::vector<std::string> get_native_system_fonts() {
    return MacOSCoreTextResolver::instance().get_system_fonts();
}

} // namespace tkblend

#endif // __APPLE__
