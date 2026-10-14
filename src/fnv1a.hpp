#pragma once

#include <cstdint>
#include <string_view>
#include <cstddef>

namespace tkblend {

// 64-bit FNV-1a constants
inline constexpr uint64_t FNV1A_64_OFFSET_BASIS = 0xcbf29ce484222325ULL;
inline constexpr uint64_t FNV1A_64_PRIME = 0x100000001b3ULL;

// 32-bit FNV-1a constants
inline constexpr uint32_t FNV1A_32_OFFSET_BASIS = 0x811c9dc5U;
inline constexpr uint32_t FNV1A_32_PRIME = 0x01000193U;

// Constexpr 64-bit FNV-1a hash of a string_view
constexpr uint64_t fnv1a64(std::string_view sv) noexcept {
    uint64_t hash = FNV1A_64_OFFSET_BASIS;
    for (char c : sv) {
        hash ^= static_cast<uint8_t>(c);
        hash *= FNV1A_64_PRIME;
    }
    return hash;
}

// Constexpr 64-bit case-insensitive FNV-1a hash of a string_view
// Maps 'A'-'Z' to 'a'-'z' in-place without dynamic memory allocation
constexpr uint64_t fnv1a64_lower(std::string_view sv) noexcept {
    uint64_t hash = FNV1A_64_OFFSET_BASIS;
    for (char c : sv) {
        uint8_t b = static_cast<uint8_t>(c);
        if (b >= 'A' && b <= 'Z') {
            b += ('a' - 'A');
        }
        hash ^= b;
        hash *= FNV1A_64_PRIME;
    }
    return hash;
}

// Constexpr 32-bit FNV-1a hash of a string_view
constexpr uint32_t fnv1a32(std::string_view sv) noexcept {
    uint32_t hash = FNV1A_32_OFFSET_BASIS;
    for (char c : sv) {
        hash ^= static_cast<uint8_t>(c);
        hash *= FNV1A_32_PRIME;
    }
    return hash;
}

// User defined literal for compile-time 64-bit FNV-1a: "key"_hash
constexpr uint64_t operator""_hash(const char* str, std::size_t len) noexcept {
    return fnv1a64(std::string_view(str, len));
}

// User defined literal for compile-time case-insensitive 64-bit FNV-1a: "Key"_hash_lower
constexpr uint64_t operator""_hash_lower(const char* str, std::size_t len) noexcept {
    return fnv1a64_lower(std::string_view(str, len));
}

} // namespace tkblend
