#include "font_resolver.hpp"

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dwrite.h>
#include <wrl/client.h>
#include <filesystem>
#include <algorithm>
#include <vector>
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

    std::string resolve(const std::string& family) {
        std::string lower = family;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        if (lower.empty() || lower == "default" || lower == "sans-serif") {
            std::string direct_match = resolve_direct_write(L"Segoe UI");
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("segoeui.ttf");
        } else if (lower == "serif") {
            std::string direct_match = resolve_direct_write(L"Times New Roman");
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("times.ttf");
        } else if (lower == "monospace") {
            std::string direct_match = resolve_direct_write(L"Consolas");
            if (!direct_match.empty()) return direct_match;
            return fallback_standard("consola.ttf");
        }

        // 1. DirectWrite primary resolution
        std::wstring wfam = utf8_to_wide(family);
        std::string path = resolve_direct_write(wfam);
        if (!path.empty()) return path;

        // 2. GDI / Registry secondary resolution
        path = resolve_registry(family);
        if (!path.empty()) return path;

        // 3. Fallback scan in standard directories
        path = fallback_file_search(lower);
        if (!path.empty()) return path;

        return "";
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

    std::string resolve_direct_write(const std::wstring& family_name) {
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

        ComPtr<IDWriteFont> font;
        hr = family->GetFont(0, font.GetAddressOf());
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

    std::string resolve_registry(const std::string& family_name) {
        std::string lower_fam = family_name;
        std::transform(lower_fam.begin(), lower_fam.end(), lower_fam.begin(), ::tolower);

        const HKEY root_keys[] = { HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER };
        const char* subkey = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts";
        std::string win_fonts = get_windows_font_dir();

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

                    // Check if key begins with the requested font family name
                    if (lower_key.rfind(lower_fam, 0) == 0) {
                        std::string target_file = reinterpret_cast<char*>(val_data);
                        std::string full_path;
                        if (target_file.find('\\') != std::string::npos || target_file.find('/') != std::string::npos) {
                            full_path = target_file;
                        } else {
                            full_path = win_fonts + target_file;
                        }

                        try {
                            if (fs::exists(full_path)) {
                                RegCloseKey(hkey);
                                return full_path;
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
        return "";
    }

    std::string fallback_file_search(const std::string& lower_family) {
        std::string win_fonts = get_windows_font_dir();
        std::string user_fonts = get_user_font_dir();
        std::vector<std::string> trial_names = {
            lower_family + ".ttf",
            lower_family + ".otf",
            lower_family + ".ttc"
        };

        for (const auto& name : trial_names) {
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
        return "";
    }

    std::string fallback_standard(const std::string& default_filename) {
        std::string p = get_windows_font_dir() + default_filename;
        try {
            if (fs::exists(p)) return p;
        } catch (...) {}
        return fallback_file_search("arial");
    }
};

} // namespace

std::string resolve_native_font_path(const std::string& family) {
    return Win32FontResolver::instance().resolve(family);
}

} // namespace tkblend

#endif // _WIN32
