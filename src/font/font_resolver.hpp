#pragma once

#include <string>
#include <vector>

namespace tkblend {

/**
 * Resolves a font family name (e.g. "DejaVu Sans", "Segoe UI", "Helvetica",
 * "sans-serif", "monospace") with optional weight (100-900) and italic style
 * to an absolute filesystem path pointing to the font file (.ttf, .otf, .ttc)
 * on the current operating system.
 *
 * Platform implementations:
 * - Windows: DirectWrite (IDWriteFactory) with GDI / Registry fallback.
 * - macOS: CoreText (CTFontDescriptor) with system font fallback.
 * - Linux / BSD: Fontconfig (FcFontList / FcFontMatch) with dlopen & candidate fallback.
 *
 * Returns an empty string if the family cannot be resolved.
 */
std::string resolve_native_font_path(const std::string& family, int weight = 400, bool italic = false);

/**
 * Returns a sorted list of unique font family names installed on the system.
 */
std::vector<std::string> get_native_system_fonts();

} // namespace tkblend
