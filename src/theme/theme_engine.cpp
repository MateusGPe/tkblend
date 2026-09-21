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
    cfg.bg_color            = 0xFF0A0F1D; // Deep obsidian slate
    cfg.fg_color            = 0xFFF1F5F9; // Crisp light text
    cfg.card_bg             = 0xFF121A2D; // Modern elevated card
    cfg.card_border         = 0xFF24304A; // Crisp 1px border
    cfg.primary_color       = 0xFF6366F1; // Electric Indigo
    cfg.primary_hover       = 0xFF818CF8;
    cfg.primary_active      = 0xFF4338CA;
    cfg.primary_fg          = 0xFFFFFFFF;
    cfg.secondary_color     = 0xFF1E283D; // Dark glass slate button
    cfg.secondary_hover     = 0xFF2A3752;
    cfg.secondary_fg        = 0xFFF1F5F9;
    cfg.destructive_color   = 0xFFEF4444; // Modern Rose / Red
    cfg.destructive_hover   = 0xFFF87171;
    cfg.destructive_active  = 0xFFDC2626;
    cfg.destructive_fg      = 0xFFFFFFFF;
    cfg.success_color       = 0xFF10B981; // Modern Emerald
    cfg.warning_color       = 0xFFF59E0B; // Amber
    cfg.input_bg            = 0xFF0D1322;
    cfg.input_border        = 0xFF24304A;
    cfg.input_focus_border  = 0xFF6366F1;
    cfg.focus_ring_color    = 0x556366F1;
    cfg.disabled_bg         = 0xFF151D2D;
    cfg.disabled_fg         = 0xFF718096;
    cfg.track_bg            = 0xFF121A2D;
    cfg.thumb_color         = 0xFF384561;
    cfg.thumb_hover         = 0xFF4D5E82;
    cfg.thumb_active        = 0xFF6366F1;
    cfg.button_radius       = 8.0;
    cfg.entry_radius        = 8.0;
    cfg.check_radius        = 5.0;
    cfg.pbar_radius         = 999.0;
    cfg.scrollbar_radius    = 999.0;
    cfg.scale_radius        = 999.0;
    cfg.scale_thumb_radius  = 9.0;
    cfg.focus_ring_width    = 2.0;
    cfg.enable_shadows      = true;
    cfg.shadow_blur         = 8.0;
    cfg.shadow_spread       = 0.0;
    cfg.shadow_offset_y     = 2.0;
    cfg.shadow_color        = 0x55000000;
    return cfg;
}

ThemeConfig ThemeConfig::create_light() {
    ThemeConfig cfg;
    cfg.dark_mode           = false;
    cfg.bg_color            = 0xFFF8FAFC; // Apple-like clean light surface
    cfg.fg_color            = 0xFF0F172A;
    cfg.card_bg             = 0xFFFFFFFF;
    cfg.card_border         = 0xFFE2E8F0;
    cfg.primary_color       = 0xFF4F46E5; // Vibrant Indigo
    cfg.primary_hover       = 0xFF6366F1;
    cfg.primary_active      = 0xFF4338CA;
    cfg.primary_fg          = 0xFFFFFFFF;
    cfg.secondary_color     = 0xFFF1F5F9;
    cfg.secondary_hover     = 0xFFE2E8F0;
    cfg.secondary_fg        = 0xFF0F172A;
    cfg.destructive_color   = 0xFFEF4444;
    cfg.destructive_hover   = 0xFFDC2626;
    cfg.destructive_active  = 0xFFB91C1C;
    cfg.destructive_fg      = 0xFFFFFFFF;
    cfg.success_color       = 0xFF059669;
    cfg.warning_color       = 0xFFD97706;
    cfg.input_bg            = 0xFFFFFFFF;
    cfg.input_border        = 0xFFCBD5E1;
    cfg.input_focus_border  = 0xFF4F46E5;
    cfg.focus_ring_color    = 0x444F46E5;
    cfg.disabled_bg         = 0xFFF1F5F9;
    cfg.disabled_fg         = 0xFF94A3B8;
    cfg.track_bg            = 0xFFE2E8F0;
    cfg.thumb_color         = 0xFFCBD5E1;
    cfg.thumb_hover         = 0xFF94A3B8;
    cfg.thumb_active        = 0xFF4F46E5;
    cfg.button_radius       = 8.0;
    cfg.entry_radius        = 8.0;
    cfg.check_radius        = 5.0;
    cfg.pbar_radius         = 999.0;
    cfg.scrollbar_radius    = 999.0;
    cfg.scale_radius        = 999.0;
    cfg.scale_thumb_radius  = 9.0;
    cfg.focus_ring_width    = 2.0;
    cfg.enable_shadows      = true;
    cfg.shadow_blur         = 8.0;
    cfg.shadow_spread       = 0.0;
    cfg.shadow_offset_y     = 2.0;
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

    // Register Blend2D custom elements (with generic and oriented names)
    Ttk_RegisterElement(interp, theme, "button", &ButtonElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Button.button", &ButtonElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Entry.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.field", &EntryFieldElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "indicator", &CheckIndicatorElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Checkbutton.indicator", &CheckIndicatorElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Radiobutton.indicator", &RadioIndicatorElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "bar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Progressbar.trough", &PbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Progressbar.pbar", &PbarBarElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scrollbar.trough", &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scrollbar.thumb", &ScrollbarThumbElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "slider", &ScaleSliderElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Scale.trough", &ScaleTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Scale.slider", &ScaleSliderElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scale.trough", &ScaleTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scale.slider", &ScaleSliderElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scale.trough", &ScaleTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scale.slider", &ScaleSliderElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "downarrow", &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.downarrow", &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.arrow", &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "uparrow", &SpinboxUpArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.uparrow", &SpinboxUpArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.downarrow", &SpinboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.buttons", &SpinboxButtonsElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "tab", &NotebookTabElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Tab.tab", &NotebookTabElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Notebook.tab", &NotebookTabElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Labelframe.border", &LabelframeBorderElementSpec, nullptr);

    // Build Tcl Theme styling script
    std::string bg      = hex_str(config_.bg_color);
    std::string fg      = hex_str(config_.fg_color);
    std::string card_bg = hex_str(config_.card_bg);
    std::string card_bd = hex_str(config_.card_border);
    std::string p_col   = hex_str(config_.primary_color);
    std::string p_fg    = hex_str(config_.primary_fg);
    std::string sec_col = hex_str(config_.secondary_color);
    std::string sec_fg  = hex_str(config_.secondary_fg);
    std::string d_col   = hex_str(config_.destructive_color);
    std::string d_fg    = hex_str(config_.destructive_fg);
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
    script << "    ttk::style configure TButton -anchor center -padding {16 7 16 7} -background \"" << sec_col << "\" -foreground \"" << sec_fg << "\"\n";
    script << "    ttk::style map TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << sec_col << "\" active \"" << sec_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << sec_fg << "\" active \"" << sec_fg << "\"]\n";

    // Accent.TButton & Primary.TButton (Electric Indigo)
    script << "    ttk::style configure Accent.TButton -anchor center -padding {16 7 16 7} -background \"" << p_col << "\" -foreground \"" << p_fg << "\"\n";
    script << "    ttk::style map Accent.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << p_col << "\" active \"" << p_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << p_fg << "\" active \"" << p_fg << "\"]\n";
    script << "    ttk::style configure Primary.TButton -anchor center -padding {16 7 16 7} -background \"" << p_col << "\" -foreground \"" << p_fg << "\"\n";
    script << "    ttk::style map Primary.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << p_col << "\" active \"" << p_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << p_fg << "\" active \"" << p_fg << "\"]\n";

    // Destructive.TButton & Danger.TButton (Rose / Red)
    script << "    ttk::style configure Destructive.TButton -anchor center -padding {16 7 16 7} -background \"" << d_col << "\" -foreground \"" << d_fg << "\"\n";
    script << "    ttk::style map Destructive.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << d_col << "\" active \"" << d_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << d_fg << "\" active \"" << d_fg << "\"]\n";
    script << "    ttk::style configure Danger.TButton -anchor center -padding {16 7 16 7} -background \"" << d_col << "\" -foreground \"" << d_fg << "\"\n";
    script << "    ttk::style map Danger.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << d_col << "\" active \"" << d_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << d_fg << "\" active \"" << d_fg << "\"]\n";

    // Secondary.TButton (Dark Glass Slate)
    script << "    ttk::style configure Secondary.TButton -anchor center -padding {16 7 16 7} -background \"" << sec_col << "\" -foreground \"" << sec_fg << "\"\n";
    script << "    ttk::style map Secondary.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << sec_col << "\" active \"" << sec_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << sec_fg << "\" active \"" << sec_fg << "\"]\n";

    // Ghost.TButton
    script << "    ttk::style configure Ghost.TButton -anchor center -padding {16 7 16 7} -background \"ghost\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style map Ghost.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << sec_col << "\" active \"" << sec_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << fg << "\" active \"" << fg << "\"]\n";

    // Outline.TButton
    script << "    ttk::style configure Outline.TButton -anchor center -padding {16 7 16 7} -background \"outline\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style map Outline.TButton \\\n"
           << "      -background [list disabled \"" << dis_bg << "\" pressed \"" << sec_col << "\" active \"" << sec_col << "\"] \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\" pressed \"" << p_col << "\" active \"" << p_col << "\"]\n";

    // TEntry Layout & Mapping
    script << "    ttk::style layout TEntry {\n"
           << "      Entry.field -sticky nswe -children {\n"
           << "        Entry.padding -sticky nswe -children {\n"
           << "          Entry.textarea -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TEntry \\\n"
           << "      -padding {10 6 10 6} \\\n"
           << "      -fieldbackground \"" << in_bg << "\" \\\n"
           << "      -foreground \"" << in_fg << "\" \\\n"
           << "      -insertcolor \"" << in_fg << "\"\n";
    script << "    ttk::style map TEntry \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"] \\\n"
           << "      -fieldbackground [list disabled \"" << dis_bg << "\"]\n";

    // TCombobox Layout & Mapping
    script << "    ttk::style layout TCombobox {\n"
           << "      Combobox.field -sticky nswe -children {\n"
           << "        Combobox.downarrow -side right -sticky ns\n"
           << "        Combobox.padding -sticky nswe -children {\n"
           << "          Combobox.textarea -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TCombobox -padding {10 6 6 6} -fieldbackground \"" << in_bg << "\" -foreground \"" << in_fg << "\" -insertcolor \"" << in_fg << "\"\n";
    script << "    ttk::style map TCombobox \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"] \\\n"
           << "      -fieldbackground [list disabled \"" << dis_bg << "\"]\n";

    // TSpinbox Layout & Mapping
    script << "    ttk::style layout TSpinbox {\n"
           << "      Spinbox.field -sticky nswe -children {\n"
           << "        Spinbox.buttons -side right -sticky ns -children {\n"
           << "          Spinbox.uparrow -side top -sticky ns\n"
           << "          Spinbox.downarrow -side bottom -sticky ns\n"
           << "        }\n"
           << "        Spinbox.padding -sticky nswe -children {\n"
           << "          Spinbox.textarea -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TSpinbox -padding {10 6 4 6} -fieldbackground \"" << in_bg << "\" -foreground \"" << in_fg << "\" -insertcolor \"" << in_fg << "\"\n";
    script << "    ttk::style map TSpinbox \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"] \\\n"
           << "      -fieldbackground [list disabled \"" << dis_bg << "\"]\n";

    // TCheckbutton Layout & Mapping
    script << "    ttk::style layout TCheckbutton {\n"
           << "      Checkbutton.padding -sticky nswe -children {\n"
           << "        Checkbutton.indicator -side left -sticky \"\"\n"
           << "        Checkbutton.focus -side left -sticky w -children {\n"
           << "          Checkbutton.label -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TCheckbutton -padding {4 4 8 4} -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
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
    script << "    ttk::style configure TRadiobutton -padding {4 4 8 4} -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
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
    script << "    ttk::style configure Horizontal.TProgressbar -thickness 12\n";
    script << "    ttk::style configure Vertical.TProgressbar -thickness 12\n";

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

    // TScale (Slider) Layout & Geometry
    script << "    ttk::style layout Horizontal.TScale {\n"
           << "      Horizontal.Scale.trough -sticky nswe -children {\n"
           << "        Horizontal.Scale.slider -side left -sticky \"\"\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style layout Vertical.TScale {\n"
           << "      Vertical.Scale.trough -sticky nswe -children {\n"
           << "        Vertical.Scale.slider -side top -sticky \"\"\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure Horizontal.TScale -sliderlength 20 -thickness 20\n";
    script << "    ttk::style configure Vertical.TScale -sliderlength 20 -thickness 20\n";

    // TLabel, TFrame, TLabelframe (Cards)
    script << "    ttk::style configure TLabel -background \"" << bg << "\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style configure TFrame -background \"" << bg << "\"\n";
    script << "    ttk::style configure Card.TFrame -background \"" << card_bg << "\"\n";
    script << "    ttk::style layout TLabelframe {\n"
           << "      Labelframe.border -sticky nswe -children {\n"
           << "        Labelframe.padding -sticky nswe -children {\n"
           << "          Labelframe.label -side top -sticky w\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TLabelframe -background \"" << card_bg << "\" -foreground \"" << fg << "\" -padding {16 12 16 12}\n";
    script << "    ttk::style configure TLabelframe.Label -background \"" << card_bg << "\" -foreground \"" << fg << "\" -font TkHeadingFont\n";

    // TNotebook (Tabs)
    script << "    ttk::style layout TNotebook {\n"
           << "      Notebook.client -sticky nswe\n"
           << "    }\n";
    script << "    ttk::style layout TNotebook.Tab {\n"
           << "      Notebook.tab -sticky nswe -children {\n"
           << "        Notebook.padding -sticky nswe -children {\n"
           << "          Notebook.label -sticky nswe\n"
           << "        }\n"
           << "      }\n"
           << "    }\n";
    script << "    ttk::style configure TNotebook -background \"" << bg << "\" -tabmargins {4 4 4 4}\n";
    script << "    ttk::style configure TNotebook.Tab -padding {16 7 16 7} -background \"" << card_bg << "\" -foreground \"" << fg << "\"\n";
    script << "    ttk::style map TNotebook.Tab -background [list selected \"" << p_col << "\" active \"" << sec_col << "\"] -foreground [list selected \"" << p_fg << "\"]\n";

    // Treeview
    script << "    ttk::style configure Treeview -background \"" << card_bg << "\" -foreground \"" << fg << "\" -fieldbackground \"" << card_bg << "\" -borderwidth 0 -rowheight 28\n";
    script << "    ttk::style configure Treeview.Heading -background \"" << in_bg << "\" -foreground \"" << fg << "\" -relief flat -padding {6 4}\n";
    script << "    ttk::style map Treeview -background [list selected \"" << p_col << "\"] -foreground [list selected \"" << p_fg << "\"]\n";

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
