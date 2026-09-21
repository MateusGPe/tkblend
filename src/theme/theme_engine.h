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
    uint32_t bg_color           = 0xFF1E1E2E; // Dark surface
    uint32_t fg_color           = 0xFFCDD6F4; // Light text
    uint32_t card_bg            = 0xFF282A36;
    uint32_t card_border        = 0xFF44475A;
    uint32_t primary_color      = 0xFF89B4FA; // Modern indigo/blue
    uint32_t primary_hover      = 0xFFB4BEFE;
    uint32_t primary_active     = 0xFF74C7EC;
    uint32_t primary_fg         = 0xFF11111B;
    uint32_t secondary_color    = 0xFF2A2B3D;
    uint32_t secondary_hover    = 0xFF383A52;
    uint32_t secondary_fg       = 0xFFE2E8F0;
    uint32_t input_bg           = 0xFF181825;
    uint32_t input_border       = 0xFF313244;
    uint32_t input_focus_border = 0xFF89B4FA;
    uint32_t focus_ring_color   = 0x6689B4FA;
    uint32_t disabled_bg        = 0xFF313244;
    uint32_t disabled_fg        = 0xFF6C7086;
    uint32_t track_bg           = 0xFF313244;
    uint32_t thumb_color        = 0xFF6C7086;
    uint32_t thumb_hover        = 0xFF9399B2;
    uint32_t thumb_active       = 0xFFB4BEFE;

    // Dimensions & Geometry
    double button_radius        = 6.0;
    double entry_radius         = 6.0;
    double check_radius         = 4.0;
    double pbar_radius          = 4.0;
    double scrollbar_radius     = 4.0;
    double focus_ring_width     = 2.0;

    // Shadow & Elevation
    bool enable_shadows         = true;
    double shadow_blur          = 6.0;
    double shadow_spread        = 0.0;
    double shadow_offset_y      = 2.0;
    uint32_t shadow_color       = 0x40000000;

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
