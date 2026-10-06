#pragma once

#include "color.hpp"
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <memory>
#include <optional>

namespace tkblend {

enum PseudoState : uint16_t {
    Normal   = 0,
    Hover    = 1 << 0,
    Active   = 1 << 1,
    Focused  = 1 << 2,
    Disabled = 1 << 3,
    Checked  = 1 << 4
};

inline PseudoState operator|(PseudoState a, PseudoState b) {
    return static_cast<PseudoState>(static_cast<uint16_t>(a) | static_cast<uint16_t>(b));
}

inline PseudoState operator&(PseudoState a, PseudoState b) {
    return static_cast<PseudoState>(static_cast<uint16_t>(a) & static_cast<uint16_t>(b));
}

inline PseudoState operator~(PseudoState a) {
    return static_cast<PseudoState>(~static_cast<uint16_t>(a));
}

struct ComputedStyle {
    Color bg_color{0, 0, 0, 0};
    Color fg_color{255, 255, 255, 255};
    Color border_color{0, 0, 0, 0};
    float border_width{0.0f};
    float border_radius{0.0f};
    float shadow_blur{0.0f};
    float shadow_offset_x{0.0f};
    float shadow_offset_y{0.0f};
    Color shadow_color{0, 0, 0, 0};
    float font_size{13.0f};
    int font_weight{400};
    std::string font_family{"sans-serif"};
};

struct StyleRule {
    std::string element;       // e.g. "button", "card", "*" or ""
    std::string class_name;    // e.g. "btn-primary", "card", or ""
    uint16_t pseudo_state = 0; // bitmask of required PseudoState
    int specificity = 0;
    std::unordered_map<std::string, std::string> declarations;
};

class StyleEngine {
public:
    static StyleEngine& instance();

    // Theme and stylesheet loading
    void set_theme(const std::string& theme_name);
    std::string get_theme() const;
    std::vector<std::string> get_available_themes() const;
    void register_theme(const std::string& theme_name, const std::string& css_text);
    void load_stylesheet(const std::string& css_text);

    // CSS Custom Property / Variable access
    void set_variable(const std::string& key, const std::string& value, const std::string& theme_name = "");
    std::string get_variable(const std::string& key, const std::string& theme_name = "") const;
    std::string resolve_var_string(const std::string& val, int depth = 0, const std::string& theme_name = "") const;

    // Color & Typed Variable resolution
    Color resolve_color(const std::string& color_str) const;
    Color resolve_color_var(const std::string& val, const Color& fallback = Color{0, 0, 0, 0}, const std::string& theme_name = "") const;
    double resolve_scalar(const std::string& val, double fallback = 0.0, const std::string& theme_name = "") const;
    std::string resolve_string(const std::string& val, const std::string& fallback = "", const std::string& theme_name = "") const;

    // Core $O(1)$ ComputedStyle resolution
    ComputedStyle resolve(
        const std::string& element,
        const std::string& class_name = "",
        uint16_t states = 0
    );

    uint32_t intern_token(const std::string& token);
    void clear_cache();

private:
    StyleEngine();
    ~StyleEngine() = default;

    void init_default_themes();
    void parse_and_apply_css(const std::string& css_text, const std::string& target_theme = "");

    mutable std::recursive_mutex mutex_;
    std::string current_theme_{"dark"};

    // Interned token mapping
    std::unordered_map<std::string, uint32_t> token_to_id_;
    std::vector<std::string> id_to_token_;
    uint32_t next_token_id_{1};

    // Per-theme variable store: theme_name -> (token_id -> value)
    std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> theme_variables_;
    std::unordered_map<std::string, std::string> theme_stylesheets_;

    // Parsed CSS Rules per theme (or shared)
    std::vector<StyleRule> global_rules_;

    // Resolution cache: combined key hash -> ComputedStyle
    std::unordered_map<uint64_t, ComputedStyle> resolve_cache_;
};

} // namespace tkblend
