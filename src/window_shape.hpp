#pragma once

#include <cstdint>

namespace tkblend {

/**
 * Returns true if the native OS window manager supports window region shaping / clipping.
 */
bool is_window_shaping_supported();

/**
 * Clips the native OS window region of a widget to a rounded rectangle.
 *
 * @param window_id Native OS window handle (X11 Window, Win32 HWND, or macOS NSView pointer).
 * @param width Pixel width of the shaped region.
 * @param height Pixel height of the shaped region.
 * @param rx Horizontal corner radius in pixels.
 * @param ry Vertical corner radius in pixels.
 * @return True on success, false on failure or if unsupported.
 */
bool apply_round_rect_shape(uint64_t window_id, int width, int height, double rx, double ry);

/**
 * Clears any applied window region shape, restoring the default rectangular window bounds.
 *
 * @param window_id Native OS window handle.
 * @return True on success, false on failure.
 */
bool clear_window_shape(uint64_t window_id);

} // namespace tkblend
