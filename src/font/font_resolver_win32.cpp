#include "font_resolver.hpp"

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dwrite.h>
#include <wrl/client.h>
#include <filesystem>
#include <algorithm>
#include <vector>
#include <set>
#include <string>
#include <mutex>

namespace fs = std::filesystem;
using Microsoft::WRL::ComPtr;

namespace tkblend {

namespace {

std::wstring utf8_to_wide(const std::string& str) {
    if (str.empty()) return L"";
    int size = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, nullptr, 0);
    if (size <= 0) return L"";
    std::wstring wstr(size - 1, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, &wstr[0], size);
    return wstr;
}

std::string wide_to_utf8(const std::wstring& wstr) {
    if (wstr.empty()) return "";
    int size = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, nullptr, 0, nullptr, nullptr);
    if (size <= 0) return "";
    std::string str(size - 1, '\0');
    WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, &str[0], size, nullptr, nullptr);
    return str;
}

std::string get_windows_font_dir() {
    std::string win_dir;
    if (const char* w = std::getenv("WINDIR")) {
        win_dir = w;
    } else if (const char* sr = std::getenv("SystemRoot")) {
        win_dir = sr;
    } else if (const char* sd = std::getenv("SystemDrive")) {
        win_dir = std::string(sd) + "\\Windows";
    } else {
        win_dir = "C:\\Windows";
    }
    return win_dir + "\\Fonts\\";
}

std::string get_user_font_dir() {
    if (const char* la = std::getenv("LOCALAPPDATA")) {
        return std::string(la) + "\\Microsoft\\Windows\\Fonts\\";
    }
    return "";
}

class Win32FontResolver {
public:
    static Win32FontResolver& instance() {
        static Win32FontResolver inst;
        return inst;
    }

    std::string resolve(const std::string& family, int weight, bool italic) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default" || lower == "sans-serif") {
            std::string direct_match = resolve_direct_write(L"Segoe UI", weight, italic);
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("segoeui.ttf", weight, italic);
        } else if (lower == "serif") {
            std::string direct_match = resolve_direct_write(L"Times New Roman", weight, italic);
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("times.ttf", weight, italic);
        } else if (lower == "monospace") {
            std::string direct_match = resolve_direct_write(L"Consolas", weight, italic);
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("consola.ttf", weight, italic);
        }

        // 1. DirectWrite primary resolution
        std::wstring wfam = utf8_to_wide(family);
        std::string path = resolve_direct_write(wfam, weight, italic);
        if (!path.empty()) return path;

        // 2. GDI / Registry secondary resolution
        path = resolve_registry(family, weight, italic);
        if (!path.empty()) return path;

        // 3. Fallback scan in standard directories
        path = fallback_file_search(lower, weight, italic);
        if (!path.empty()) return path;

        return "";
    }

    std::vector<std::string> get_system_fonts() {
        std::lock_guard<std::mutex> lock(mutex_);
        ensure_direct_write();

        std::set<std::string> unique_families;
        if (font_collection_) {
            UINT32 family_count = font_collection_->GetFontFamilyCount();
            for (UINT32 i = 0; i < family_count; ++i) {
                ComPtr<IDWriteFontFamily> family;
                if (SUCCEEDED(font_collection_->GetFontFamily(i, family.GetAddressOf())) && family) {
                    ComPtr<IDWriteLocalizedStrings> names;
                    if (SUCCEEDED(family->GetFamilyNames(names.GetAddressOf())) && names) {
                        UINT32 name_count = names->GetCount();
                        for (UINT32 j = 0; j < name_count; ++j) {
                            UINT32 len = 0;
                            if (SUCCEEDED(names->GetStringLength(j, &len))) {
                                std::wstring wname(len + 1, L'\0');
                                if (SUCCEEDED(names->GetString(j, &wname[0], len + 1))) {
                                    wname.resize(len);
                                    std::string u8 = wide_to_utf8(wname);
                                    if (!u8.empty()) {
                                        unique_families.insert(u8);
                                        break; // Keep first/default localization
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        if (unique_families.empty()) {
            // Registry fallback enumeration
            const HKEY root_keys[] = { HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER };
            const char* subkey = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts";
            for (HKEY root : root_keys) {
                HKEY hkey = nullptr;
                if (RegOpenKeyExA(root, subkey, 0, KEY_READ, &hkey) == ERROR_SUCCESS) {
                    char val_name[512];
                    BYTE val_data[512];
                    DWORD val_name_size = sizeof(val_name);
                    DWORD val_data_size = sizeof(val_data);
                    DWORD type = 0;
                    DWORD idx = 0;
                    while (RegEnumValueA(hkey, idx, val_name, &val_name_size, nullptr, &type, val_data, &val_data_size) == ERROR_SUCCESS) {
                        if (type == REG_SZ) {
                            std::string s(val_name);
                            size_t paren = s.find(" (");
                            if (paren != std::string::npos) {
                                s = s.substr(0, paren);
                            }
                            if (!s.empty()) unique_families.insert(s);
                        }
                        val_name_size = sizeof(val_name);
                        val_data_size = sizeof(val_data);
                        idx++;
                    }
                    RegCloseKey(hkey);
                }
            }
        }

        return std::vector<std::string>(unique_families.begin(), unique_families.end());
    }

private:
    std::mutex mutex_;
    ComPtr<IDWriteFactory> dwrite_factory_;
    ComPtr<IDWriteFontCollection> font_collection_;
    bool dwrite_init_attempted_ = false;

    Win32FontResolver() = default;

    void ensure_direct_write() {
        if (dwrite_init_attempted_) return;
        dwrite_init_attempted_ = true;

        HRESULT hr = DWriteCreateFactory(
            DWRITE_FACTORY_TYPE_SHARED,
            __uuidof(IDWriteFactory),
            reinterpret_cast<IUnknown**>(dwrite_factory_.GetAddressOf())
        );

        if (SUCCEEDED(hr) && dwrite_factory_) {
            dwrite_factory_->GetSystemFontCollection(font_collection_.GetAddressOf(), FALSE);
        }
    }

    std::string resolve_direct_write(const std::wstring& family_name, int weight, bool italic) {
        std::lock_guard<std::mutex> lock(mutex_);
        ensure_direct_write();
        if (!font_collection_) return "";

        UINT32 index = 0;
        BOOL exists = FALSE;
        HRESULT hr = font_collection_->FindFamilyName(family_name.c_str(), &index, &exists);
        if (FAILED(hr) || !exists) return "";

        ComPtr<IDWriteFontFamily> family;
        hr = font_collection_->GetFontFamily(index, family.GetAddressOf());
        if (FAILED(hr) || !family) return "";

        DWRITE_FONT_WEIGHT dw_weight = static_cast<DWRITE_FONT_WEIGHT>(weight);
        DWRITE_FONT_STYLE dw_style = italic ? DWRITE_FONT_STYLE_ITALIC : DWRITE_FONT_STYLE_NORMAL;

        ComPtr<IDWriteFont> font;
        hr = family->GetFirstMatchingFont(dw_weight, DWRITE_FONT_STRETCH_NORMAL, dw_style, font.GetAddressOf());
        if (FAILED(hr) || !font) {
            hr = family->GetFont(0, font.GetAddressOf());
        }
        if (FAILED(hr) || !font) return "";

        ComPtr<IDWriteFontFace> font_face;
        hr = font->CreateFontFace(font_face.GetAddressOf());
        if (FAILED(hr) || !font_face) return "";

        UINT32 file_count = 0;
        hr = font_face->GetFiles(&file_count, nullptr);
        if (FAILED(hr) || file_count == 0) return "";

        std::vector<IDWriteFontFile*> raw_files(file_count, nullptr);
        hr = font_face->GetFiles(&file_count, raw_files.data());
        if (FAILED(hr)) return "";

        std::string result_path;
        if (raw_files[0]) {
            const void* ref_key = nullptr;
            UINT32 key_size = 0;
            if (SUCCEEDED(raw_files[0]->GetReferenceKey(&ref_key, &key_size))) {
                ComPtr<IDWriteFontFileLoader> loader;
                if (SUCCEEDED(raw_files[0]->GetLoader(loader.GetAddressOf())) && loader) {
                    ComPtr<IDWriteLocalFontFileLoader> local_loader;
                    if (SUCCEEDED(loader.As(&local_loader)) && local_loader) {
                        UINT32 path_len = 0;
                        if (SUCCEEDED(local_loader->GetFilePathLengthFromKey(ref_key, key_size, &path_len))) {
                            std::wstring wpath(path_len + 1, L'\0');
                            if (SUCCEEDED(local_loader->GetFilePathFromKey(ref_key, key_size, &wpath[0], path_len + 1))) {
                                wpath.resize(path_len);
                                std::string resolved = wide_to_utf8(wpath);
                                try {
                                    if (fs::exists(resolved)) {
                                        result_path = resolved;
                                    }
                                } catch (...) {}
                            }
                        }
                    }
                }
            }
        }

        for (auto* f : raw_files) {
            if (f) f->Release();
        }

        return result_path;
    }

    std::string resolve_registry(const std::string& family_name, int weight, bool italic) {
        std::string lower_fam = family_name;
        std::transform(lower_fam.begin(), lower_fam.end(), lower_fam.begin(), ::tolower);

        const HKEY root_keys[] = { HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER };
        const char* subkey = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts";
        std::string win_fonts = get_windows_font_dir();
        std::string fallback_candidate;

        for (HKEY root : root_keys) {
            HKEY hkey = nullptr;
            if (RegOpenKeyExA(root, subkey, 0, KEY_READ, &hkey) != ERROR_SUCCESS) {
                continue;
            }

            char val_name[512];
            BYTE val_data[512];
            DWORD val_name_size = sizeof(val_name);
            DWORD val_data_size = sizeof(val_data);
            DWORD type = 0;
            DWORD idx = 0;

            while (RegEnumValueA(hkey, idx, val_name, &val_name_size, nullptr, &type, val_data, &val_data_size) == ERROR_SUCCESS) {
                if (type == REG_SZ) {
                    std::string key_str(val_name);
                    std::string lower_key = key_str;
                    std::transform(lower_key.begin(), lower_key.end(), lower_key.begin(), ::tolower);

                    if (lower_key.rfind(lower_fam, 0) == 0) {
                        std::string target_file = reinterpret_cast<char*>(val_data);
                        std::string full_path = (target_file.find('\\') != std::string::npos || target_file.find('/') != std::string::npos)
                            ? target_file : win_fonts + target_file;

                        try {
                            if (fs::exists(full_path)) {
                                if (fallback_candidate.empty()) {
                                    fallback_candidate = full_path;
                                }

                                bool is_bold = (lower_key.find("bold") != std::string::npos);
                                bool is_italic = (lower_key.find("italic") != std::string::npos || lower_key.find("oblique") != std::string::npos);

                                if (is_bold == (weight >= 600) && is_italic == italic) {
                                    RegCloseKey(hkey);
                                    return full_path;
                                }
                            }
                        } catch (...) {}
                    }
                }

                val_name_size = sizeof(val_name);
                val_data_size = sizeof(val_data);
                idx++;
            }

            RegCloseKey(hkey);
        }
        return fallback_candidate;
    }

    std::string fallback_file_search(const std::string& lower_family, int weight, bool italic) {
        std::string win_fonts = get_windows_font_dir();
        std::string user_fonts = get_user_font_dir();
        std::vector<std::string> suffixes;
        if (weight >= 600 && italic) suffixes = { "bi", "-bolditalic", "_bolditalic", "z" };
        else if (weight >= 600) suffixes = { "bd", "-bold", "_bold", "b" };
        else if (italic) suffixes = { "i", "-italic", "_italic" };
        suffixes.push_back("");

        for (const auto& suf : suffixes) {
            for (const char* ext : { ".ttf", ".otf", ".ttc" }) {
                std::string name = lower_family + suf + ext;
                std::string p1 = win_fonts + name;
                try {
                    if (fs::exists(p1)) return p1;
                } catch (...) {}
                if (!user_fonts.empty()) {
                    std::string p2 = user_fonts + name;
                    try {
                        if (fs::exists(p2)) return p2;
                    } catch (...) {}
                }
            }
        }
        return "";
    }

    std::string fallback_standard(const std::string& default_filename, int weight, bool italic) {
        std::string p = get_windows_font_dir() + default_filename;
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
        return fallback_file_search("arial", weight, italic);
    }
};

} // namespace

std::string resolve_native_font_path(const std::string& family, int weight, bool italic) {
    return Win32FontResolver::instance().resolve(family, weight, italic);
}

std::vector<std::string> get_native_system_fonts() {
    return Win32FontResolver::instance().get_system_fonts();
}

} // namespace tkblend

#endif // _WIN32
