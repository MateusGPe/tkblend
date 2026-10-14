#pragma once

#include <string_view>
#include <array>
#include <cstdint>
#include <charconv>
#include <cstdlib>
#include <algorithm>

namespace tkblend {

// -----------------------------------------------------------------------------
// Compile-time Hex Look-Up Table (LUT)
// -----------------------------------------------------------------------------
inline constexpr auto kHexLut = []() consteval {
    std::array<uint8_t, 256> lut{};
    for (size_t i = 0; i < 256; ++i) {
        lut[i] = 0xFF; // Invalid marker
    }
    for (char c = '0'; c <= '9'; ++c) {
        lut[static_cast<uint8_t>(c)] = static_cast<uint8_t>(c - '0');
    }
    for (char c = 'a'; c <= 'f'; ++c) {
        lut[static_cast<uint8_t>(c)] = static_cast<uint8_t>(c - 'a' + 10);
    }
    for (char c = 'A'; c <= 'F'; ++c) {
        lut[static_cast<uint8_t>(c)] = static_cast<uint8_t>(c - 'A' + 10);
    }
    return lut;
}();

inline constexpr bool is_hex_char(char c) noexcept {
    return kHexLut[static_cast<uint8_t>(c)] != 0xFF;
}

inline constexpr uint8_t hex_to_nibble(char c) noexcept {
    uint8_t val = kHexLut[static_cast<uint8_t>(c)];
    return (val == 0xFF) ? 0 : val;
}

inline constexpr uint8_t parse_2hex(char c1, char c2) noexcept {
    return static_cast<uint8_t>((hex_to_nibble(c1) << 4) | hex_to_nibble(c2));
}

inline constexpr uint8_t parse_1hex(char c) noexcept {
    return static_cast<uint8_t>(hex_to_nibble(c) * 17);
}

// -----------------------------------------------------------------------------
// In-place string_view utilities (Zero-allocation)
// -----------------------------------------------------------------------------
inline constexpr std::string_view trim_view(std::string_view sv) noexcept {
    while (!sv.empty() && static_cast<unsigned char>(sv.front()) <= 32) {
        sv.remove_prefix(1);
    }
    while (!sv.empty() && static_cast<unsigned char>(sv.back()) <= 32) {
        sv.remove_suffix(1);
    }
    return sv;
}

inline constexpr std::string_view strip_quotes_view(std::string_view sv) noexcept {
    sv = trim_view(sv);
    if (sv.size() >= 2) {
        if ((sv.front() == '"' && sv.back() == '"') || (sv.front() == '\'' && sv.back() == '\'')) {
            return sv.substr(1, sv.size() - 2);
        }
    }
    return sv;
}

// Extracts inner variable identifier from "var(--name, fallback)" or "--name" or "name"
// If has_fallback is non-null, it receives the fallback string_view if present
inline constexpr std::string_view extract_var_view(
    std::string_view raw,
    std::string_view* fallback_out = nullptr
) noexcept {
    std::string_view s = trim_view(raw);
    if (fallback_out) *fallback_out = {};

    if (s.starts_with("var(") && s.ends_with(')')) {
        s = s.substr(4, s.size() - 5);
        size_t comma = s.find(',');
        if (comma != std::string_view::npos) {
            if (fallback_out) {
                *fallback_out = trim_view(s.substr(comma + 1));
            }
            s = s.substr(0, comma);
        }
        s = trim_view(s);
    }

    if (s.starts_with("--")) {
        s.remove_prefix(2);
    }
    return s;
}

// Fast string_view number parsing
inline double fast_parse_double(std::string_view sv, double fallback = 0.0) noexcept {
    sv = trim_view(sv);
    if (sv.empty()) return fallback;

    // Use fast stack buffer for strtod if needed
    char buf[64];
    if (sv.size() < sizeof(buf)) {
        std::copy(sv.begin(), sv.end(), buf);
        buf[sv.size()] = '\0';
        char* end = nullptr;
        double val = std::strtod(buf, &end);
        if (end != buf) return val;
    }
    return fallback;
}

inline float fast_parse_float(std::string_view sv, float fallback = 0.0f) noexcept {
    return static_cast<float>(fast_parse_double(sv, static_cast<double>(fallback)));
}

inline int fast_parse_int(std::string_view sv, int fallback = 0) noexcept {
    sv = trim_view(sv);
    if (sv.empty()) return fallback;
    int val = 0;
    auto [ptr, ec] = std::from_chars(sv.data(), sv.data() + sv.size(), val);
    if (ec == std::errc()) {
        return val;
    }
    return fallback;
}

// Fast CSS length parser (e.g., "12px", "14.5", "2em")
inline float fast_parse_length(std::string_view sv, float fallback = 0.0f) noexcept {
    sv = trim_view(sv);
    if (sv.empty()) return fallback;
    if (sv == "none" || sv == "0" || sv == "0px") return 0.0f;

    // Strip trailing px, pt, etc.
    if (sv.ends_with("px") || sv.ends_with("pt")) {
        sv.remove_suffix(2);
    }
    return fast_parse_float(sv, fallback);
}

} // namespace tkblend
