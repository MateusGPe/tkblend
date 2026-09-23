#pragma once

#include "platform_compat.h"
#include <cstdint>
#include <string>
#include <memory>
#include <mutex>

namespace tkblend {

struct ThemeConfig {
    bool dark_mode = true;

    // Palette Colors (ARGB) - Default: Catppuccin Mocha
    uint32_t bg_color           = 0xFF11111B; // Mocha Crust
    uint32_t fg_color           = 0xFFCDD6F4; // Mocha Text
    uint32_t card_bg            = 0xFF1E1E2E; // Mocha Base
    uint32_t card_border        = 0xFF313244; // Mocha Surface0
    uint32_t primary_color      = 0xFF89B4FA; // Mocha Blue
    uint32_t primary_hover      = 0xFFB4BEFE; // Mocha Lavender
    uint32_t primary_active     = 0xFF74C7EC; // Mocha Sapphire
    uint32_t primary_fg         = 0xFF11111B; // Mocha Crust (contrast)
    uint32_t secondary_color    = 0xFF313244; // Mocha Surface0
    uint32_t secondary_hover    = 0xFF45475A; // Mocha Surface1
    uint32_t secondary_fg       = 0xFFCDD6F4; // Mocha Text
    uint32_t destructive_color  = 0xFFF38BA8; // Mocha Red
    uint32_t destructive_hover  = 0xFFF5E0DC; // Mocha Rosewater
    uint32_t destructive_active = 0xFFEBA0AC; // Mocha Maroon
    uint32_t destructive_fg     = 0xFF11111B; // Mocha Crust
    uint32_t success_color      = 0xFFA6E3A1; // Mocha Green
    uint32_t warning_color      = 0xFFFAB387; // Mocha Peach
    uint32_t input_bg           = 0xFF181825; // Mocha Mantle
    uint32_t input_border       = 0xFF313244; // Mocha Surface0
    uint32_t input_focus_border = 0xFF89B4FA; // Mocha Blue
    uint32_t focus_ring_color   = 0x5589B4FA;
    uint32_t disabled_bg        = 0xFF181825; // Mocha Mantle
    uint32_t disabled_fg        = 0xFF6C7086; // Mocha Overlay0
    uint32_t track_bg           = 0xFF313244; // Mocha Surface0
    uint32_t thumb_color        = 0xFF585B70; // Mocha Surface2
    uint32_t thumb_hover        = 0xFF6C7086; // Mocha Overlay0
    uint32_t thumb_active       = 0xFF89B4FA; // Mocha Blue

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
