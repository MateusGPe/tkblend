#pragma once

#include "platform_compat.h"
#include <cstdint>
#include <string>
#include <memory>
#include <mutex>

namespace tkblend {

struct ThemeConfig {
    bool dark_mode = true;

    // Palette Colors (ARGB)
    uint32_t bg_color           = 0xFF0A0F1D; // Deep obsidian slate
    uint32_t fg_color           = 0xFFF1F5F9; // Crisp light text
    uint32_t card_bg            = 0xFF121A2D; // Modern elevated card
    uint32_t card_border        = 0xFF24304A; // Crisp 1px border
    uint32_t primary_color      = 0xFF6366F1; // Electric Indigo
    uint32_t primary_hover      = 0xFF818CF8;
    uint32_t primary_active     = 0xFF4338CA;
    uint32_t primary_fg         = 0xFFFFFFFF;
    uint32_t secondary_color    = 0xFF1E283D; // Dark glass slate button
    uint32_t secondary_hover    = 0xFF2A3752;
    uint32_t secondary_fg       = 0xFFF1F5F9;
    uint32_t destructive_color  = 0xFFEF4444; // Modern rose / red
    uint32_t destructive_hover  = 0xFFF87171;
    uint32_t destructive_active = 0xFFDC2626;
    uint32_t destructive_fg     = 0xFFFFFFFF;
    uint32_t success_color      = 0xFF10B981; // Modern Emerald
    uint32_t warning_color      = 0xFFF59E0B; // Amber
    uint32_t input_bg           = 0xFF0D1322;
    uint32_t input_border       = 0xFF24304A;
    uint32_t input_focus_border = 0xFF6366F1;
    uint32_t focus_ring_color   = 0x556366F1;
    uint32_t disabled_bg        = 0xFF151D2D;
    uint32_t disabled_fg        = 0xFF5B6987;
    uint32_t track_bg           = 0xFF121A2D;
    uint32_t thumb_color        = 0xFF384561;
    uint32_t thumb_hover        = 0xFF4D5E82;
    uint32_t thumb_active       = 0xFF6366F1;

    // Dimensions & Geometry
    double button_radius        = 8.0;
    double entry_radius         = 8.0;
    double check_radius         = 5.0;
    double pbar_radius          = 999.0;
    double scrollbar_radius     = 999.0;
    double scale_radius         = 999.0;
    double scale_thumb_radius   = 9.0;
    double focus_ring_width     = 2.0;

    // Shadow & Elevation
    bool enable_shadows         = true;
    double shadow_blur          = 8.0;
    double shadow_spread        = 0.0;
    double shadow_offset_y      = 2.0;
    uint32_t shadow_color       = 0x55000000;

    static ThemeConfig create_dark();
    static ThemeConfig create_light();
};

class ThemeEngine {
public:
    static ThemeEngine& instance();

    const ThemeConfig& config() const { return config_; }
    void set_config(const ThemeConfig& cfg);
    void set_dark_mode(bool dark);

    // Register all elements and create theme in Tcl interpreter
    bool init_ttk_theme(Tcl_Interp* interp, const char* theme_name = "tkblend");

private:
    ThemeEngine();
    ThemeConfig config_;
    mutable std::mutex mutex_;
    bool registered_ = false;
};

// C export for pure Tcl `package require tkblend_theme` or `load`
TKBLEND_API int Tkblend_theme_Init(Tcl_Interp *interp);
TKBLEND_API int Tkblend_theme_SafeInit(Tcl_Interp *interp);

} // namespace tkblend
