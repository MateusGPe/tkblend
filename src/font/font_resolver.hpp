#pragma once

#include <string>

namespace tkblend {

/**
 * Resolves a font family name (e.g. "DejaVu Sans", "Segoe UI", "Helvetica",
 * "sans-serif", "monospace") to an absolute filesystem path pointing to the
 * font file (.ttf, .otf, .ttc) on the current operating system.
 *
 * Platform implementations:
 * - Windows: DirectWrite (IDWriteFactory) with GDI / Registry fallback.
 * - macOS: CoreText (CTFontDescriptor) with system font fallback.
 * - Linux / BSD: Fontconfig (FcFontList / FcFontMatch) with system candidate fallback.
 *
 * Returns an empty string if the family cannot be resolved.
 */
std::string resolve_native_font_path(const std::string& family);

} // namespace tkblend
