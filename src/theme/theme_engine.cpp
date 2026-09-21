#include "theme_engine.h"
#include "element_common.h"
#include <sstream>
#include <iomanip>

#ifdef USE_TTK_STUBS
const TtkStubs *ttkStubsPtr = nullptr;

extern "C" const char *
TtkInitializeStubs(
    Tcl_Interp *interp, const char *version, int epoch, int revision)
{
    int exact = 0;
    const void *stubsPtr = nullptr;
    const char *actualVersion = Tcl_PkgRequireEx(interp, "Ttk", version, exact, const_cast<void**>(&stubsPtr));

    if (!actualVersion) {
        return nullptr;
    }
    if (!stubsPtr) {
        Tcl_SetResult(interp, const_cast<char*>("This implementation of Ttk does not support stubs"), TCL_STATIC);
        return nullptr;
    }
    ttkStubsPtr = static_cast<const TtkStubs*>(stubsPtr);
    if (ttkStubsPtr->epoch != epoch || ttkStubsPtr->revision < revision) {
        Tcl_SetResult(interp, const_cast<char*>("Version mismatch: this version of Ttk is not compatible"), TCL_STATIC);
        return nullptr;
    }
    return actualVersion;
}
#endif

namespace tkblend {

ThemeConfig ThemeConfig::create_dark() {
    ThemeConfig cfg;
    cfg.dark_mode           = true;
    cfg.bg_color            = 0xFF181824; // Deep sleek dark slate
    cfg.fg_color            = 0xFFE2E8F0; // Crisp light text
    cfg.card_bg             = 0xFF20212E; // Modern dark card
    cfg.card_border         = 0xFF323548;
    cfg.primary_color       = 0xFF3B82F6; // Vibrant modern blue
    cfg.primary_hover       = 0xFF60A5FA;
    cfg.primary_active      = 0xFF2563EB;
    cfg.primary_fg          = 0xFFFFFFFF;
    cfg.secondary_color     = 0xFF2A2B3D; // Dark button surface
    cfg.secondary_hover     = 0xFF383A52;
    cfg.secondary_fg        = 0xFFE2E8F0;
    cfg.input_bg            = 0xFF14141E;
    cfg.input_border        = 0xFF383A52;
    cfg.input_focus_border  = 0xFF3B82F6;
    cfg.focus_ring_color    = 0x443B82F6;
    cfg.disabled_bg         = 0xFF1E1E2A;
    cfg.disabled_fg         = 0xFF5A5D7A;
    cfg.track_bg            = 0xFF14141E;
    cfg.thumb_color         = 0xFF40435C;
    cfg.thumb_hover         = 0xFF565A7C;
    cfg.thumb_active        = 0xFF3B82F6;
    cfg.button_radius       = 7.0;
    cfg.entry_radius        = 6.0;
    cfg.check_radius        = 4.5;
    cfg.pbar_radius         = 5.0;
    cfg.scrollbar_radius    = 5.0;
    cfg.enable_shadows      = true;
    cfg.shadow_blur         = 6.0;
    cfg.shadow_color        = 0x35000000;
    return cfg;
}

ThemeConfig ThemeConfig::create_light() {
    ThemeConfig cfg;
    cfg.dark_mode           = false;
    cfg.bg_color            = 0xFFF8FAFC; // Apple-like clean light surface
    cfg.fg_color            = 0xFF0F172A;
    cfg.card_bg             = 0xFFFFFFFF;
    cfg.card_border         = 0xFFE2E8F0;
    cfg.primary_color       = 0xFF2563EB; // Modern macOS/iOS vibrant blue
    cfg.primary_hover       = 0xFF3B82F6;
    cfg.primary_active      = 0xFF1D4ED8;
    cfg.primary_fg          = 0xFFFFFFFF;
    cfg.secondary_color     = 0xFFF1F5F9;
    cfg.secondary_hover     = 0xFFE2E8F0;
    cfg.secondary_fg        = 0xFF0F172A;
    cfg.input_bg            = 0xFFFFFFFF;
    cfg.input_border        = 0xFFCBD5E1;
    cfg.input_focus_border  = 0xFF2563EB;
    cfg.focus_ring_color    = 0x442563EB;
    cfg.disabled_bg         = 0xFFF1F5F9;
    cfg.disabled_fg         = 0xFF94A3B8;
    cfg.track_bg            = 0xFFE2E8F0;
    cfg.thumb_color         = 0xFFCBD5E1;
    cfg.thumb_hover         = 0xFF94A3B8;
    cfg.thumb_active        = 0xFF2563EB;
    cfg.button_radius       = 7.0;
    cfg.entry_radius        = 6.0;
    cfg.check_radius        = 4.5;
    cfg.pbar_radius         = 5.0;
    cfg.scrollbar_radius    = 5.0;
    cfg.enable_shadows      = true;
    cfg.shadow_blur         = 6.0;
    cfg.shadow_color        = 0x1A000000;
    return cfg;
}

ThemeEngine& ThemeEngine::instance() {
    static ThemeEngine engine;
    return engine;
}

ThemeEngine::ThemeEngine()
    : config_(ThemeConfig::create_dark()) {}

void ThemeEngine::set_config(const ThemeConfig& cfg) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_ = cfg;
}

void ThemeEngine::set_dark_mode(bool dark) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (dark) {
        config_ = ThemeConfig::create_dark();
    } else {
        config_ = ThemeConfig::create_light();
    }
}

static std::string hex_str(uint32_t argb) {
    std::ostringstream ss;
    ss << "#" << std::hex << std::setfill('0') << std::setw(6) << (argb & 0x00FFFFFF);
    return ss.str();
}

bool ThemeEngine::init_ttk_theme(Tcl_Interp* interp, const char* theme_name) {
    if (!interp) return false;

    // Ensure Tcl/Tk Stubs are initialized
    #if USE_TCL_STUBS
    if (!Tcl_InitStubs(interp, "8.5", 0)) {
        return false;
    }
    #endif
    #if USE_TK_STUBS
    if (!Tk_InitStubs(interp, "8.5", 0)) {
        return false;
    }
    #endif
    #if USE_TTK_STUBS
    if (!Ttk_InitStubs(interp)) {
        return false;
    }
    #endif

    std::lock_guard<std::mutex> lock(mutex_);

    // Get default or parent theme
    Ttk_Theme parentTheme = Ttk_GetDefaultTheme(interp);
    Ttk_Theme theme = Ttk_CreateTheme(interp, theme_name, parentTheme);
    if (!theme) {
        theme = Ttk_GetTheme(interp, theme_name);
    }
    if (!theme) {
        return false;
    }

    // Register Blend2D custom elements (with both generic and oriented names)
    Ttk_RegisterElementSpec(theme, "Button.button", &ButtonElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Entry.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Combobox.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Spinbox.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Checkbutton.indicator", &CheckIndicatorElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Radiobutton.indicator", &RadioIndicatorElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Horizontal.Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Horizontal.Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Vertical.Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Vertical.Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Horizontal.Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Horizontal.Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Vertical.Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElementSpec(theme, "Vertical.Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);

    // Build Tcl Theme styling script
    std::string bg      = hex_str(config_.bg_color);
    std::string fg      = hex_str(config_.fg_color);
    std::string card_bg = hex_str(config_.card_bg);
    std::string card_bd = hex_str(config_.card_border);
    std::string p_col   = hex_str(config_.primary_color);
    std::string p_fg    = hex_str(config_.primary_fg);
    std::string sec_col = hex_str(config_.secondary_color);
    std::string sec_fg  = hex_str(config_.secondary_fg);
    std::string dis_fg  = hex_str(config_.disabled_fg);
    std::string dis_bg  = hex_str(config_.disabled_bg);
    std::string in_bg   = hex_str(config_.input_bg);
    std::string in_fg   = hex_str(config_.fg_color);
    std::string sel_bg  = hex_str(config_.primary_color);
    std::string sel_fg  = hex_str(config_.primary_fg);

    std::ostringstream script;
    script << "namespace eval ttk::theme::" << theme_name << " {\n";
    script << "  ttk::style theme settings " << theme_name << " {\n";

    // General defaults
    script << "    ttk::style configure . \\\n"
           << "      -background \"" << bg << "\" \\\n"
           << "      -foreground \"" << fg << "\" \\\n"
           << "      -troughcolor \"" << bg << "\" \\\n"
           << "      -selectbackground \"" << sel_bg << "\" \\\n"
           << "      -selectforeground \"" << sel_fg << "\" \\\n"
           << "      -insertcolor \"" << fg << "\" \\\n"
           << "      -borderwidth 0\n";

    // Global map for disabled states
    script << "    ttk::style map . \\\n"
           << "      -background [list disabled \"" << dis_bg << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TButton Layout & Mapping
    script << "    ttk::style layout TButton {\n"
           << "      Button.button -sticky nswe -children {\n"
           << "        Button.padding -sticky nswe -children {\n"
           << "          Button.label -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TButton -anchor center -padding {14 6 14 6} -foreground \"" << sec_fg << "\"\n";
    script << "    ttk::style map TButton \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // Accent.TButton & Primary.TButton (Vibrant Accent Buttons)
    script << "    ttk::style configure Accent.TButton -anchor center -padding {14 6 14 6} -foreground \"" << p_fg << "\"\n";
    script << "    ttk::style map Accent.TButton -foreground [list disabled \"" << dis_fg << "\"]\n";
    script << "    ttk::style configure Primary.TButton -anchor center -padding {14 6 14 6} -foreground \"" << p_fg << "\"\n";
    script << "    ttk::style map Primary.TButton -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TEntry Layout & Mapping
    script << "    ttk::style layout TEntry {\n"
           << "      Entry.field -sticky nswe -children {\n"
           << "        Entry.padding -sticky nswe -children {\n"
           << "          Entry.textarea -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TEntry \\\n"
           << "      -padding {8 5 8 5} \\\n"
           << "      -fieldbackground \"" << in_bg << "\" \\\n"
           << "      -foreground \"" << in_fg << "\" \\\n"
           << "      -insertcolor \"" << in_fg << "\"\n";
    script << "    ttk::style map TEntry \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TCombobox & TSpinbox Layouts
    script << "    ttk::style configure TCombobox -padding {8 5 8 5} -fieldbackground \"" << in_bg << "\" -foreground \"" << in_fg << "\" -insertcolor \"" << in_fg << "\"\n";
    script << "    ttk::style configure TSpinbox -padding {8 5 8 5} -fieldbackground \"" << in_bg << "\" -foreground \"" << in_fg << "\" -insertcolor \"" << in_fg << "\"\n";

    // TCheckbutton Layout & Mapping
    script << "    ttk::style layout TCheckbutton {\n"
           << "      Checkbutton.padding -sticky nswe -children {\n"
           << "        Checkbutton.indicator -side left -sticky \"\"\n"
           << "        Checkbutton.focus -side left -sticky w -children {\n"
           << "          Checkbutton.label -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TCheckbutton -padding {4 3 6 3} -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style map TCheckbutton \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TRadiobutton Layout & Mapping
    script << "    ttk::style layout TRadiobutton {\n"
           << "      Radiobutton.padding -sticky nswe -children {\n"
           << "        Radiobutton.indicator -side left -sticky \"\"\n"
           << "        Radiobutton.focus -side left -sticky w -children {\n"
           << "          Radiobutton.label -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TRadiobutton -padding {4 3 6 3} -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style map TRadiobutton \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TProgressbar Layout & Geometry
    script << "    ttk::style layout Horizontal.TProgressbar {\n"
           << "      Horizontal.Progressbar.trough -sticky nswe -children {\n"
           << "        Horizontal.Progressbar.pbar -side left -sticky ns\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style layout Vertical.TProgressbar {\n"
           << "      Vertical.Progressbar.trough -sticky nswe -children {\n"
           << "        Vertical.Progressbar.pbar -side bottom -sticky we\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure Horizontal.TProgressbar -thickness 10\n";
    script << "    ttk::style configure Vertical.TProgressbar -thickness 10\n";

    // TScrollbar Layout & Geometry
    script << "    ttk::style layout Horizontal.TScrollbar {\n"
           << "      Horizontal.Scrollbar.trough -sticky we -children {\n"
           << "        Horizontal.Scrollbar.thumb -sticky nswe\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style layout Vertical.TScrollbar {\n"
           << "      Vertical.Scrollbar.trough -sticky ns -children {\n"
           << "        Vertical.Scrollbar.thumb -sticky nswe\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure Horizontal.TScrollbar -arrowsize 0\n";
    script << "    ttk::style configure Vertical.TScrollbar -arrowsize 0\n";

    // TLabel, TFrame, TLabelframe configurations
    script << "    ttk::style configure TLabel -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style configure TFrame -background \"" << bg << "\"\n";
    script << "    ttk::style configure TLabelframe -background \"" << bg << "\" -foreground \"" << fg << "\" -borderwidth 1 -relief solid\n";
    script << "    ttk::style configure TLabelframe.Label -background \"" << bg << "\" -foreground \"" << fg << "\"\n";

    // TNotebook (Tabs)
    script << "    ttk::style configure TNotebook -background \"" << bg << "\" -tabmargins {2 2 2 0}\n";
    script << "    ttk::style configure TNotebook.Tab -background \"" << card_bg << "\" -foreground \"" << fg << "\" -padding {12 6}\n";
    script << "    ttk::style map TNotebook.Tab -background [list selected \"" << p_col << "\" active \"" << sec_col << "\"] -foreground [list selected \"" << p_fg << "\"]\n";

    script << "  }\n";
    script << "}\n";

    int code = Tcl_Eval(interp, script.str().c_str());
    if (code != TCL_OK) {
        return false;
    }

    registered_ = true;
    return true;
}

TKBLEND_API int Tkblend_theme_Init(Tcl_Interp *interp) {
    if (!ThemeEngine::instance().init_ttk_theme(interp, "tkblend")) {
        return TCL_ERROR;
    }
    return Tcl_PkgProvide(interp, "tkblend_theme", "1.0");
}

TKBLEND_API int Tkblend_theme_SafeInit(Tcl_Interp *interp) {
    return Tkblend_theme_Init(interp);
}

} // namespace tkblend
