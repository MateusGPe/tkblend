#pragma once

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

namespace tkblend {

struct EmbeddedFont {
    const char* name;
    const char* family;
    const uint8_t* compressed_data;
    size_t compressed_size;
    size_t uncompressed_size;
};

// Returns list of all embedded font descriptors
const std::vector<EmbeddedFont>& get_embedded_fonts();

// Decompresses an embedded font into an in-memory byte buffer
bool decompress_embedded_font(const EmbeddedFont& font, std::vector<uint8_t>& out_bytes);

} // namespace tkblend
