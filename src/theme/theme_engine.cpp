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
    config_ = dark ? ThemeConfig::create_dark() : ThemeConfig::create_light();
}

static std::string hex_str(uint32_t argb) {
    std::ostringstream ss;
    ss << "#" << std::hex << std::setfill('0') << std::setw(6) << (argb & 0x00FFFFFF);
    return ss.str();
}

// ---------------------------------------------------------------------------
// StyleScript — DRY builder for ttk::style configure / map / layout calls.
// Encapsulates the repetitive ostringstream patterns in init_ttk_theme.
// ---------------------------------------------------------------------------
struct StyleScript {
    std::ostringstream ss;

    /// Emit a ttk::style configure line with arbitrary options string.
    void configure(const std::string& style, const std::string& opts) {
        ss << "    ttk::style configure " << style << " " << opts << "\n";
    }

    /// Emit a standard three-state map for a single property.
    void map_states(const std::string& style, const std::string& prop,
                    const std::string& disabled_val,
                    const std::string& pressed_val,
                    const std::string& active_val) {
        ss << "    ttk::style map " << style << " \\\n"
           << "      -" << prop << " [list"
           << " disabled \"" << disabled_val << "\""
           << " pressed \"" << pressed_val << "\""
           << " active \"" << active_val << "\"]\n";
    }

    /// Emit configure + two-state (bg + fg) map for a button-like widget.
    void button_style(const std::string& style,
                      const std::string& bg,   const std::string& fg,
                      const std::string& dis_bg, const std::string& dis_fg,
                      const std::string& pressed_bg, const std::string& pressed_fg,
                      const std::string& active_bg, const std::string& active_fg,
                      const std::string& variant = "") {
        std::string var_opt = variant.empty() ? "" : (" -variant \"" + variant + "\"");
        configure(style, "-anchor center -padding {16 7 16 7}" + var_opt +
                  " -background \"" + bg + "\" -foreground \"" + fg + "\"");
        ss << "    ttk::style map " << style << " \\\n"
           << "      -background [list"
           << " disabled \"" << dis_bg << "\""
           << " pressed \"" << pressed_bg << "\""
           << " active \"" << active_bg << "\"] \\\n"
           << "      -foreground [list"
           << " disabled \"" << dis_fg << "\""
           << " pressed \"" << pressed_fg << "\""
           << " active \"" << active_fg << "\"]\n";
    }

    /// Emit configure + map for an input-like widget (Entry, Combobox, Spinbox).
    void input_style(const std::string& style, const std::string& padding,
                     const std::string& field_bg, const std::string& fg,
                     const std::string& insert_col,
                     const std::string& sel_bg, const std::string& sel_fg,
                     const std::string& dis_fg, const std::string& dis_bg) {
        ss << "    ttk::style configure " << style
           << " -padding " << padding
           << " -fieldbackground \"" << field_bg << "\""
           << " -foreground \"" << fg << "\""
           << " -insertcolor \"" << insert_col << "\""
           << " -selectbackground \"" << sel_bg << "\""
           << " -selectforeground \"" << sel_fg << "\"\n";
        ss << "    ttk::style map " << style << " \\\n"
           << "      -foreground [list disabled \"" << dis_fg << "\"] \\\n"
           << "      -fieldbackground [list disabled \"" << dis_bg << "\"]\n";
    }

    /// Emit a scrollbar layout + configure pair (avoids 4× duplication).
    void scrollbar_style(const std::string& orient_prefix,
                         const std::string& style_prefix,
                         const std::string& trough_sticky,
                         int thickness) {
        std::string trough = orient_prefix + ".Scrollbar.trough";
        std::string thumb  = orient_prefix + ".Scrollbar.thumb";
        std::string style  = style_prefix + "." + orient_prefix + ".TScrollbar";
        ss << "    ttk::style layout " << style << " {\n"
           << "      " << trough << " -sticky " << trough_sticky << " -children {\n"
           << "        " << thumb << " -sticky nswe\n"
           << "      }\n"
           << "    }\n";
        ss << "    ttk::style configure " << style
           << " -arrowsize 0 -thickness " << thickness << "\n";
    }

    std::string str() const { return ss.str(); }
};

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
    Ttk_RegisterElement(interp, theme, "button",                          &ButtonElementSpec,          nullptr);
    Ttk_RegisterElement(interp, theme, "Button.button",                   &ButtonElementSpec,          nullptr);
    Ttk_RegisterElement(interp, theme, "field",                           &EntryFieldElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Entry.field",                     &EntryFieldElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.field",                  &EntryFieldElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.field",                   &EntryFieldElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "indicator",                       &CheckIndicatorElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Checkbutton.indicator",           &CheckIndicatorElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Radiobutton.indicator",           &RadioIndicatorElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "trough",                          &PbarTroughElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "pbar",                            &PbarBarElementSpec,         nullptr);
    Ttk_RegisterElement(interp, theme, "bar",                             &PbarBarElementSpec,         nullptr);
    Ttk_RegisterElement(interp, theme, "Progressbar.trough",              &PbarTroughElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Progressbar.pbar",                &PbarBarElementSpec,         nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Progressbar.trough",   &PbarTroughElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Progressbar.pbar",     &PbarBarElementSpec,         nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Progressbar.trough",     &PbarTroughElementSpec,      nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Progressbar.pbar",       &PbarBarElementSpec,         nullptr);
    Ttk_RegisterElement(interp, theme, "thumb",                           &ScrollbarThumbElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Scrollbar.trough",                &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Scrollbar.thumb",                 &ScrollbarThumbElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scrollbar.trough",     &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scrollbar.thumb",      &ScrollbarThumbElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scrollbar.trough",       &ScrollbarTroughElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scrollbar.thumb",        &ScrollbarThumbElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "slider",                          &ScaleSliderElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Scale.trough",                    &ScaleTroughElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Scale.slider",                    &ScaleSliderElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scale.trough",         &ScaleTroughElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Horizontal.Scale.slider",         &ScaleSliderElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scale.trough",           &ScaleTroughElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Vertical.Scale.slider",           &ScaleSliderElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "downarrow",                       &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.downarrow",              &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Combobox.arrow",                  &ComboboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "uparrow",                         &SpinboxUpArrowElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.uparrow",                 &SpinboxUpArrowElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.downarrow",               &SpinboxDownArrowElementSpec, nullptr);
    Ttk_RegisterElement(interp, theme, "Spinbox.buttons",                 &SpinboxButtonsElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "tab",                             &NotebookTabElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Tab.tab",                         &NotebookTabElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "Notebook.tab",                    &NotebookTabElementSpec,     nullptr);
    Ttk_RegisterElement(interp, theme, "client",                          &NotebookClientElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Notebook.client",                 &NotebookClientElementSpec,  nullptr);
    Ttk_RegisterElement(interp, theme, "Labelframe.border",               &LabelframeBorderElementSpec, nullptr);

    // Resolve color tokens once
    const std::string bg      = hex_str(config_.bg_color);
    const std::string fg      = hex_str(config_.fg_color);
    const std::string card_bg = hex_str(config_.card_bg);
    const std::string card_bd = hex_str(config_.card_border);
    const std::string p_col   = hex_str(config_.primary_color);
    const std::string p_fg    = hex_str(config_.primary_fg);
    const std::string sec_col = hex_str(config_.secondary_color);
    const std::string sec_fg  = hex_str(config_.secondary_fg);
    const std::string d_col   = hex_str(config_.destructive_color);
    const std::string d_fg    = hex_str(config_.destructive_fg);
    const std::string dis_fg  = hex_str(config_.disabled_fg);
    const std::string dis_bg  = hex_str(config_.disabled_bg);
    const std::string in_bg   = hex_str(config_.input_bg);
    const std::string in_fg   = hex_str(config_.fg_color);
    const std::string sel_bg  = hex_str(config_.primary_color);
    const std::string sel_fg  = hex_str(config_.primary_fg);

    StyleScript s;
    s.ss << "namespace eval ttk::theme::" << theme_name << " {\n";
    s.ss << "  ttk::style theme settings " << theme_name << " {\n";

    // General defaults
    s.ss << "    ttk::style configure . \\\n"
         << "      -background \""   << bg      << "\" \\\n"
         << "      -foreground \""   << fg      << "\" \\\n"
         << "      -troughcolor \""  << bg      << "\" \\\n"
         << "      -selectbackground \"" << sel_bg << "\" \\\n"
         << "      -selectforeground \"" << sel_fg << "\" \\\n"
         << "      -insertcolor \""  << fg      << "\" \\\n"
         << "      -borderwidth 0\n";

    // Global disabled state map
    s.ss << "    ttk::style map . \\\n"
         << "      -background [list disabled \"" << dis_bg << "\"] \\\n"
         << "      -foreground [list disabled \"" << dis_fg << "\"]\n";

    // TButton layout
    s.ss << "    ttk::style layout TButton {\n"
         << "      Button.button -sticky nswe -children {\n"
         << "        Button.padding -sticky nswe -children {\n"
         << "          Button.label -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";

    // Button variants (Standard / Secondary / Accent=Primary / Destructive / Ghost / Outline)
    s.button_style("TButton",           sec_col, sec_fg, dis_bg, dis_fg, sec_col, sec_fg, sec_col, sec_fg);
    s.button_style("Accent.TButton",    p_col,   p_fg,   dis_bg, dis_fg, p_col,   p_fg,   p_col,   p_fg);
    s.button_style("Primary.TButton",   p_col,   p_fg,   dis_bg, dis_fg, p_col,   p_fg,   p_col,   p_fg);
    s.button_style("Destructive.TButton", d_col, d_fg,   dis_bg, dis_fg, d_col,   d_fg,   d_col,   d_fg);
    s.button_style("Danger.TButton",    d_col,   d_fg,   dis_bg, dis_fg, d_col,   d_fg,   d_col,   d_fg);
    s.button_style("Secondary.TButton", sec_col, sec_fg, dis_bg, dis_fg, sec_col, sec_fg, sec_col, sec_fg);
    s.button_style("Ghost.TButton",   card_bg, fg, dis_bg, dis_fg, sec_col, fg,    sec_col, fg,    "ghost");
    s.button_style("Outline.TButton", card_bg, fg, dis_bg, dis_fg, sec_col, p_col, sec_col, p_col, "outline");

    // TEntry layout
    s.ss << "    ttk::style layout TEntry {\n"
         << "      Entry.field -sticky nswe -children {\n"
         << "        Entry.padding -sticky nswe -children {\n"
         << "          Entry.textarea -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.input_style("TEntry",    "{10 6 10 6}", in_bg, in_fg, in_fg, sel_bg, sel_fg, dis_fg, dis_bg);

    // TCombobox layout
    s.ss << "    ttk::style layout TCombobox {\n"
         << "      Combobox.field -sticky nswe -children {\n"
         << "        Combobox.downarrow -side right -sticky ns\n"
         << "        Combobox.padding -sticky nswe -children {\n"
         << "          Combobox.textarea -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.input_style("TCombobox", "{10 6 6 6}",  in_bg, in_fg, in_fg, sel_bg, sel_fg, dis_fg, dis_bg);

    // TSpinbox layout
    s.ss << "    ttk::style layout TSpinbox {\n"
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
    s.input_style("TSpinbox",  "{10 6 4 6}",  in_bg, in_fg, in_fg, sel_bg, sel_fg, dis_fg, dis_bg);

    // TCheckbutton
    s.ss << "    ttk::style layout TCheckbutton {\n"
         << "      Checkbutton.padding -sticky nswe -children {\n"
         << "        Checkbutton.indicator -side left -sticky \"\"\n"
         << "        Checkbutton.focus -side left -sticky w -children {\n"
         << "          Checkbutton.label -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.configure("TCheckbutton", "-padding {4 4 8 4} -background \"" + bg + "\" -foreground \"" + fg + "\"");
    s.map_states("TCheckbutton", "foreground", dis_fg, fg, fg);
    s.configure("Card.TCheckbutton", "-padding {4 4 8 4} -background \"" + card_bg + "\" -foreground \"" + fg + "\"");
    s.map_states("Card.TCheckbutton", "foreground", dis_fg, fg, fg);

    // TRadiobutton
    s.ss << "    ttk::style layout TRadiobutton {\n"
         << "      Radiobutton.padding -sticky nswe -children {\n"
         << "        Radiobutton.indicator -side left -sticky \"\"\n"
         << "        Radiobutton.focus -side left -sticky w -children {\n"
         << "          Radiobutton.label -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.configure("TRadiobutton", "-padding {4 4 8 4} -background \"" + bg + "\" -foreground \"" + fg + "\"");
    s.map_states("TRadiobutton", "foreground", dis_fg, fg, fg);
    s.configure("Card.TRadiobutton", "-padding {4 4 8 4} -background \"" + card_bg + "\" -foreground \"" + fg + "\"");
    s.map_states("Card.TRadiobutton", "foreground", dis_fg, fg, fg);

    // TProgressbar layouts & geometry
    s.ss << "    ttk::style layout Horizontal.TProgressbar {\n"
         << "      Horizontal.Progressbar.trough -sticky nswe -children {\n"
         << "        Horizontal.Progressbar.pbar -side left -sticky ns\n"
         << "      }\n"
         << "    }\n"
         << "    ttk::style layout Vertical.TProgressbar {\n"
         << "      Vertical.Progressbar.trough -sticky nswe -children {\n"
         << "        Vertical.Progressbar.pbar -side bottom -sticky we\n"
         << "      }\n"
         << "    }\n";
    s.configure("Horizontal.TProgressbar", "-thickness 12");
    s.configure("Vertical.TProgressbar",   "-thickness 12");

    // TScrollbar — standard (12px) and floating overlay (6px idle / 10px hover)
    for (const auto& orient : std::initializer_list<std::pair<const char*, const char*>>{
            {"Horizontal", "we"}, {"Vertical", "ns"}}) {
        s.scrollbar_style(orient.first, "",       orient.second, 12);
        s.scrollbar_style(orient.first, "Floating", orient.second, 6);
        s.scrollbar_style(orient.first, "Hover.Floating", orient.second, 10);
    }

    // TScale layouts & geometry
    s.ss << "    ttk::style layout Horizontal.TScale {\n"
         << "      Horizontal.Scale.trough -sticky nswe -children {\n"
         << "        Horizontal.Scale.slider -side left -sticky \"\"\n"
         << "      }\n"
         << "    }\n"
         << "    ttk::style layout Vertical.TScale {\n"
         << "      Vertical.Scale.trough -sticky nswe -children {\n"
         << "        Vertical.Scale.slider -side top -sticky \"\"\n"
         << "      }\n"
         << "    }\n";
    s.configure("Horizontal.TScale", "-sliderlength 20 -thickness 20");
    s.configure("Vertical.TScale",   "-sliderlength 20 -thickness 20");

    // TLabel, TFrame, TLabelframe (Cards)
    s.configure("TLabel",           "-background \"" + bg      + "\" -foreground \"" + fg + "\"");
    s.configure("Card.TLabel",      "-background \"" + card_bg + "\" -foreground \"" + fg + "\"");
    s.configure("TFrame",           "-background \"" + bg      + "\"");
    s.configure("Card.TFrame",      "-background \"" + card_bg + "\"");
    s.ss << "    ttk::style layout TLabelframe {\n"
         << "      Labelframe.border -sticky nswe -children {\n"
         << "        Labelframe.padding -sticky nswe -children {\n"
         << "          Labelframe.label -side top -sticky w\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.configure("TLabelframe",       "-background \"" + card_bg + "\" -foreground \"" + fg + "\" -padding {16 12 16 12}");
    s.configure("TLabelframe.Label", "-background \"" + card_bg + "\" -foreground \"" + fg + "\" -font TkHeadingFont");

    // TNotebook (Tabs)
    s.ss << "    ttk::style layout TNotebook {\n"
         << "      Notebook.client -sticky nswe\n"
         << "    }\n"
         << "    ttk::style layout TNotebook.Tab {\n"
         << "      Notebook.tab -sticky nswe -children {\n"
         << "        Notebook.padding -sticky nswe -children {\n"
         << "          Notebook.label -sticky nswe\n"
         << "        }\n"
         << "      }\n"
         << "    }\n";
    s.configure("TNotebook",     "-background \"" + bg + "\" -tabmargins {4 4 4 4}");
    s.configure("TNotebook.Tab", "-padding {16 7 16 7} -background \"" + card_bg + "\" -foreground \"" + fg + "\"");
    s.ss << "    ttk::style map TNotebook.Tab"
         << " -background [list selected \"" << p_col << "\" active \"" << sec_col << "\"]"
         << " -foreground [list selected \"" << p_fg << "\"]\n";

    // Treeview
    s.configure("Treeview",
        "-background \"" + card_bg + "\" -foreground \"" + fg +
        "\" -fieldbackground \"" + card_bg + "\" -borderwidth 0 -rowheight 28");
    s.configure("Treeview.Heading",
        "-background \"" + in_bg + "\" -foreground \"" + fg + "\" -relief flat -padding {6 4}");
    s.ss << "    ttk::style map Treeview"
         << " -background [list selected \"" << p_col << "\"]"
         << " -foreground [list selected \"" << p_fg << "\"]\n";

    s.ss << "  }\n}\n";

    // Dynamic Option Database for Combobox Popdown Listbox
    s.ss << "option add *TCombobox*Listbox.background \""     << in_bg  << "\" widgetDefault\n"
         << "option add *TCombobox*Listbox.foreground \""     << in_fg  << "\" widgetDefault\n"
         << "option add *TCombobox*Listbox.selectBackground \"" << sel_bg << "\" widgetDefault\n"
         << "option add *TCombobox*Listbox.selectForeground \"" << sel_fg << "\" widgetDefault\n"
         << "option add *TCombobox*Listbox.borderWidth 1 widgetDefault\n"
         << "option add *TCombobox*Listbox.relief flat widgetDefault\n"
         << "option add *TCombobox*Listbox.highlightThickness 0 widgetDefault\n";

    const std::string script = s.str();
    if (Tcl_Eval(interp, script.c_str()) != TCL_OK) {
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
