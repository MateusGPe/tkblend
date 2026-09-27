#!/usr/bin/env python3
"""
Generate embedded C++ font buffers and Python icon definitions for tkblend.
Bundles Font Awesome 6 Free (Solid, Regular, Brands) and Lucide Icons.
"""

import os
import sys
import ssl
import json
import zlib
import struct
import urllib.request
from typing import Dict, Tuple

FONTS = {
    "fa_solid": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.ttf",
        "family": "Font Awesome 6 Free Solid",
        "alias": "fa-solid",
    },
    "fa_regular": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.ttf",
        "family": "Font Awesome 6 Free Regular",
        "alias": "fa-regular",
    },
    "fa_brands": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.ttf",
        "family": "Font Awesome 6 Brands Regular",
        "alias": "fa-brands",
    },
    "lucide": {
        "url": "https://unpkg.com/lucide-static@latest/font/lucide.ttf",
        "family": "lucide",
        "alias": "lucide",
    }
}


def download_font(url: str) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tkblend/embedded-fonts)"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        return resp.read()


def parse_ttf_glyph_map(ttf_data: bytes) -> Dict[str, int]:
    """Extract glyph name -> unicode codepoint from TTF tables."""
    num_tables = struct.unpack(">H", ttf_data[4:6])[0]
    tables = {}
    for i in range(num_tables):
        tag = ttf_data[12 + i * 16 : 12 + i * 16 + 4].decode("latin1")
        offset, length = struct.unpack(">II", ttf_data[12 + i * 16 + 8 : 12 + i * 16 + 16])
        tables[tag] = (offset, length)

    glyph_names = {}
    if "post" in tables:
        post_off, post_len = tables["post"]
        post_format = struct.unpack(">I", ttf_data[post_off : post_off + 4])[0]
        if post_format == 0x00020000:
            num_glyphs = struct.unpack(">H", ttf_data[post_off + 32 : post_off + 34])[0]
            glyph_indices = struct.unpack(f">{num_glyphs}H", ttf_data[post_off + 34 : post_off + 34 + num_glyphs * 2])
            p = post_off + 34 + num_glyphs * 2
            pascal_strings = []
            while p < post_off + post_len:
                s_len = ttf_data[p]
                p += 1
                s = ttf_data[p : p + s_len].decode("latin1")
                p += s_len
                pascal_strings.append(s)
            for g_id, s_idx in enumerate(glyph_indices):
                if s_idx >= 258 and (s_idx - 258) < len(pascal_strings):
                    glyph_names[g_id] = pascal_strings[s_idx - 258]

    unicode_to_gid = {}
    if "cmap" in tables:
        cmap_off, cmap_len = tables["cmap"]
        version, num_subtables = struct.unpack(">HH", ttf_data[cmap_off : cmap_off + 4])
        for s in range(num_subtables):
            platform_id, encoding_id, sub_off = struct.unpack(">HHI", ttf_data[cmap_off + 4 + s * 8 : cmap_off + 4 + (s + 1) * 8])
            sub_pos = cmap_off + sub_off
            sub_format = struct.unpack(">H", ttf_data[sub_pos : sub_pos + 2])[0]
            if sub_format == 4:
                length, lang, seg_count_x2 = struct.unpack(">HHH", ttf_data[sub_pos + 2 : sub_pos + 8])
                seg_count = seg_count_x2 // 2
                end_codes = struct.unpack(f">{seg_count}H", ttf_data[sub_pos + 14 : sub_pos + 14 + seg_count * 2])
                start_codes = struct.unpack(f">{seg_count}H", ttf_data[sub_pos + 16 + seg_count * 2 : sub_pos + 16 + seg_count * 4])
                id_deltas = struct.unpack(f">{seg_count}h", ttf_data[sub_pos + 16 + seg_count * 4 : sub_pos + 16 + seg_count * 6])
                id_range_offsets = struct.unpack(f">{seg_count}H", ttf_data[sub_pos + 16 + seg_count * 6 : sub_pos + 16 + seg_count * 8])

                for i in range(seg_count):
                    start = start_codes[i]
                    end = end_codes[i]
                    delta = id_deltas[i]
                    ro = id_range_offsets[i]
                    if start == 0xFFFF:
                        continue
                    for cp in range(start, end + 1):
                        if ro == 0:
                            gid = (cp + delta) & 0xFFFF
                        else:
                            ro_pos = sub_pos + 16 + seg_count * 6 + i * 2 + ro + (cp - start) * 2
                            gid = struct.unpack(">H", ttf_data[ro_pos : ro_pos + 2])[0]
                            if gid != 0:
                                gid = (gid + delta) & 0xFFFF
                        if gid != 0 and cp not in unicode_to_gid:
                            unicode_to_gid[cp] = gid

    gid_to_unicode = {gid: cp for cp, gid in unicode_to_gid.items()}
    name_to_cp = {}
    for gid, name in glyph_names.items():
        if gid in gid_to_unicode:
            name_to_cp[name] = gid_to_unicode[gid]

    return name_to_cp


def generate_header(font_binaries: Dict[str, Tuple[dict, bytes]], out_hpp: str, out_cpp: str):
    hpp_content = """#pragma once

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
"""

    cpp_chunks = [
        '#include "embedded_fonts.hpp"',
        '#include <zlib.h>',
        '#include <stdexcept>',
        '#include <iostream>',
        '',
        'namespace tkblend {',
        ''
    ]

    descriptors = []
    for key, (meta, data) in font_binaries.items():
        compressed = zlib.compress(data, level=9)
        var_name = f"k_{key}_data"
        cpp_chunks.append(f"// Embedded {meta['family']} ({len(data)} uncompressed bytes -> {len(compressed)} compressed)")
        cpp_chunks.append(f"static const uint8_t {var_name}[{len(compressed)}] = {{")
        
        # Write bytes in chunks of 16
        for i in range(0, len(compressed), 16):
            chunk = compressed[i : i + 16]
            hex_str = ", ".join(f"0x{b:02x}" for b in chunk)
            cpp_chunks.append(f"    {hex_str},")
        cpp_chunks.append("};\n")

        descriptors.append(
            f'        EmbeddedFont{{"{meta["alias"]}", "{meta["family"]}", {var_name}, sizeof({var_name}), {len(data)}}}'
        )

    cpp_chunks.append("const std::vector<EmbeddedFont>& get_embedded_fonts() {")
    cpp_chunks.append("    static const std::vector<EmbeddedFont> fonts = {")
    cpp_chunks.append(",\n".join(descriptors))
    cpp_chunks.append("    };")
    cpp_chunks.append("    return fonts;")
    cpp_chunks.append("}\n")

    cpp_chunks.append("""bool decompress_embedded_font(const EmbeddedFont& font, std::vector<uint8_t>& out_bytes) {
    out_bytes.resize(font.uncompressed_size);
    uLongf dest_len = static_cast<uLongf>(font.uncompressed_size);
    int res = uncompress(
        out_bytes.data(),
        &dest_len,
        font.compressed_data,
        static_cast<uLong>(font.compressed_size)
    );
    if (res != Z_OK || dest_len != font.uncompressed_size) {
        out_bytes.clear();
        return false;
    }
    return true;
}

} // namespace tkblend
""")

    os.makedirs(os.path.dirname(out_hpp), exist_ok=True)
    os.makedirs(os.path.dirname(out_cpp), exist_ok=True)

    with open(out_hpp, "w", encoding="utf-8") as f:
        f.write(hpp_content)

    with open(out_cpp, "w", encoding="utf-8") as f:
        f.write("\n".join(cpp_chunks))

    print(f"Generated C++ headers: {out_hpp} and {out_cpp}")


def generate_python_icons(icon_maps: Dict[str, Dict[str, int]], out_py: str):
    lines = [
        '"""',
        'Icon registry and helper constants for tkblend.',
        'Supports Font Awesome 6 Free (Solid, Regular, Brands) and Lucide Icons.',
        '"""',
        '',
        'from __future__ import annotations',
        'import re',
        'from typing import Optional, Dict, Tuple, Any',
        '',
        '# Icon mappings: name -> unicode character',
    ]

    for key, mapping in icon_maps.items():
        var_name = f"{key.upper()}_MAP"
        lines.append(f"{var_name}: Dict[str, str] = {{")
        for name, cp in sorted(mapping.items()):
            char_repr = repr(chr(cp))
            lines.append(f'    "{name}": {char_repr},')
        lines.append("}\n")

    lines.append("""
class _IconGroup:
    def __init__(self, mapping: Dict[str, str], prefix: str):
        self._mapping = mapping
        self._prefix = prefix

    def __getattr__(self, name: str) -> str:
        clean_name = name.lower().replace("_", "-")
        if clean_name in self._mapping:
            return self._mapping[clean_name]
        raise AttributeError(f"Icon '{name}' not found in {self._prefix}")

    def __getitem__(self, name: str) -> str:
        clean_name = name.lower().replace("_", "-")
        if clean_name in self._mapping:
            return self._mapping[clean_name]
        raise KeyError(f"Icon '{name}' not found in {self._prefix}")

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        clean_name = name.lower().replace("_", "-")
        return self._mapping.get(clean_name, default)

    def __contains__(self, name: str) -> bool:
        clean_name = name.lower().replace("_", "-")
        return clean_name in self._mapping


FA_SOLID = _IconGroup(FA_SOLID_MAP, "fa-solid")
FA_REGULAR = _IconGroup(FA_REGULAR_MAP, "fa-regular")
FA_BRANDS = _IconGroup(FA_BRANDS_MAP, "fa-brands")
LUCIDE = _IconGroup(LUCIDE_MAP, "lucide")


class Icons:
    \"\"\"
    Convenient namespace for all icon sets and top-level icon access.
    \"\"\"
    SOLID = FA_SOLID
    REGULAR = FA_REGULAR
    BRANDS = FA_BRANDS
    LUCIDE = LUCIDE

    # Direct access helpers
    ROCKET = FA_SOLID_MAP.get("rocket", LUCIDE_MAP.get("rocket", "🚀"))
    SEARCH = FA_SOLID_MAP.get("magnifying-glass", LUCIDE_MAP.get("search", "🔍"))
    SETTINGS = FA_SOLID_MAP.get("gear", LUCIDE_MAP.get("settings", "⚙️"))
    HEART = FA_SOLID_MAP.get("heart", LUCIDE_MAP.get("heart", "❤️"))
    CHECK = FA_SOLID_MAP.get("check", LUCIDE_MAP.get("check", "✓"))
    CLOSE = FA_SOLID_MAP.get("xmark", LUCIDE_MAP.get("x", "✕"))
    SPARKLES = LUCIDE_MAP.get("sparkles", "✨")
    SUN = LUCIDE_MAP.get("sun", "☀️")
    MOON = LUCIDE_MAP.get("moon", "🌙")
    FOLDER = FA_SOLID_MAP.get("folder", LUCIDE_MAP.get("folder", "📁"))
    FILE = FA_SOLID_MAP.get("file", LUCIDE_MAP.get("file", "📄"))
    USER = FA_SOLID_MAP.get("user", LUCIDE_MAP.get("user", "👤"))

    @classmethod
    def get(cls, name: str, default: str = "") -> str:
        \"\"\"
        Lookup an icon by name with optional prefix, e.g.
        'fa:rocket', 'fa-solid:rocket', 'lucide:sparkles', 'rocket'.
        \"\"\"
        clean = name.strip().lower()
        if ":" in clean:
            prefix, icon_name = clean.split(":", 1)
            icon_name = icon_name.replace("_", "-")
            if prefix in ("fa", "fa-solid", "solid"):
                return FA_SOLID_MAP.get(icon_name, default)
            elif prefix in ("fa-regular", "regular"):
                return FA_REGULAR_MAP.get(icon_name, default)
            elif prefix in ("fa-brands", "brands"):
                return FA_BRANDS_MAP.get(icon_name, default)
            elif prefix == "lucide":
                return LUCIDE_MAP.get(icon_name, default)
        
        # Search all maps
        icon_name = clean.replace("_", "-")
        for m in (FA_SOLID_MAP, LUCIDE_MAP, FA_REGULAR_MAP, FA_BRANDS_MAP):
            if icon_name in m:
                return m[icon_name]
        return default


_MARKUP_REGEX = re.compile(r"(?::([a-zA-Z0-9_\-]+(?::[a-zA-Z0-9_\-]+)?):)|(?:\{([a-zA-Z0-9_\-]+(?::[a-zA-Z0-9_\-]+)?)\})")


def parse_icon_markup(text: str) -> str:
    \"\"\"
    Replaces inline icon markup such as ':fa:rocket:', ':lucide:sparkles:',
    '{fa:rocket}', '{settings}' with the corresponding unicode icon character.
    \"\"\"
    if not text:
        return text

    def _replace(match: re.Match) -> str:
        key = match.group(1) or match.group(2)
        icon_char = Icons.get(key)
        if icon_char:
            return icon_char
        return match.group(0)

    return _MARKUP_REGEX.sub(_replace, text)
""")

    os.makedirs(os.path.dirname(out_py), exist_ok=True)
    with open(out_py, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated Python icons: {out_py}")


def main():
    print("Fetching and parsing icon fonts...")
    font_binaries = {}
    icon_maps = {}

    for key, meta in FONTS.items():
        print(f"Downloading {meta['family']} from {meta['url']}...")
        data = download_font(meta["url"])
        print(f"Downloaded {len(data)} bytes.")
        font_binaries[key] = (meta, data)
        mapping = parse_ttf_glyph_map(data)
        print(f"Parsed {len(mapping)} glyph mappings for {key}.")
        icon_maps[key] = mapping

    generate_header(
        font_binaries,
        "src/font/embedded_fonts.hpp",
        "src/font/embedded_fonts.cpp"
    )
    generate_python_icons(icon_maps, "tkblend/icons.py")
    print("Done!")


if __name__ == "__main__":
    main()
