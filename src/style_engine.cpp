#include "style_engine.hpp"
#include "default_styles.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <iostream>

namespace tkblend {

namespace {

inline std::string trim(const std::string& str) {
    auto start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    auto end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

inline std::string to_lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
}

inline std::string strip_quotes(const std::string& s) {
    std::string t = trim(s);
    if (t.size() >= 2 && ((t.front() == '"' && t.back() == '"') || (t.front() == '\'' && t.back() == '\''))) {
        return t.substr(1, t.size() - 2);
    }
    return t;
}

inline float parse_length(const std::string& s) {
    std::string t = trim(s);
    if (t.empty()) return 0.0f;
    try {
        size_t idx = 0;
        float val = std::stof(t, &idx);
        if (!std::isfinite(val)) return 0.0f;
        return val;
    } catch (...) {
        return 0.0f;
    }
}

// Convert HSL to RGB
Color hsl_to_color(double h, double s, double l, double a = 1.0) {
    h = std::fmod(h, 360.0);
    if (h < 0.0) h += 360.0;
    s = std::clamp(s, 0.0, 1.0);
    l = std::clamp(l, 0.0, 1.0);

    double c = (1.0 - std::abs(2.0 * l - 1.0)) * s;
    double x = c * (1.0 - std::abs(std::fmod(h / 60.0, 2.0) - 1.0));
    double m = l - c / 2.0;

    double r1 = 0, g1 = 0, b1 = 0;
    if (h < 60.0) { r1 = c; g1 = x; b1 = 0; }
    else if (h < 120.0) { r1 = x; g1 = c; b1 = 0; }
    else if (h < 180.0) { r1 = 0; g1 = c; b1 = x; }
    else if (h < 240.0) { r1 = 0; g1 = x; b1 = c; }
    else if (h < 300.0) { r1 = x; g1 = 0; b1 = c; }
    else { r1 = c; g1 = 0; b1 = x; }

    uint8_t r = static_cast<uint8_t>(std::clamp((r1 + m) * 255.0 + 0.5, 0.0, 255.0));
    uint8_t g = static_cast<uint8_t>(std::clamp((g1 + m) * 255.0 + 0.5, 0.0, 255.0));
    uint8_t b = static_cast<uint8_t>(std::clamp((b1 + m) * 255.0 + 0.5, 0.0, 255.0));
    uint8_t alpha = static_cast<uint8_t>(std::clamp(a * 255.0 + 0.5, 0.0, 255.0));
    return Color(r, g, b, alpha);
}

// Split on a delimiter, ignoring delimiters inside parentheses or quotes.
inline std::vector<std::string> split_top_level(const std::string& s, char delim) {
    std::vector<std::string> out;
    std::string cur;
    int depth = 0;
    char quote = 0;
    for (char c : s) {
        if (quote) {
            cur.push_back(c);
            if (c == quote) quote = 0;
            continue;
        }
        if (c == '"' || c == '\'') {
            quote = c;
            cur.push_back(c);
            continue;
        }
        if (c == '(') ++depth;
        else if (c == ')' && depth > 0) --depth;
        if (c == delim && depth == 0) {
            out.push_back(cur);
            cur.clear();
            continue;
        }
        cur.push_back(c);
    }
    out.push_back(cur);
    return out;
}

// Fast match of named CSS colors via compile-time FNV-1a switch
static constexpr std::optional<Color> match_named_color(std::string_view name) noexcept {
    switch (fnv1a64_lower(name)) {
        case "transparent"_hash: return Color(0, 0, 0, 0);
        case "none"_hash:        return Color(0, 0, 0, 0);
        case "white"_hash:       return Color(255, 255, 255, 255);
        case "black"_hash:       return Color(0, 0, 0, 255);
        case "red"_hash:         return Color(255, 0, 0, 255);
        case "green"_hash:       return Color(0, 255, 0, 255);
        case "blue"_hash:        return Color(0, 0, 255, 255);
        case "yellow"_hash:      return Color(255, 255, 0, 255);
        case "cyan"_hash:
        case "aqua"_hash:        return Color(0, 255, 255, 255);
        case "magenta"_hash:     return Color(255, 0, 255, 255);
        case "gray"_hash:
        case "grey"_hash:        return Color(128, 128, 128, 255);
        case "silver"_hash:      return Color(192, 192, 192, 255);
        case "maroon"_hash:      return Color(128, 0, 0, 255);
        case "olive"_hash:       return Color(128, 128, 0, 255);
        case "lime"_hash:        return Color(0, 255, 0, 255);
        case "teal"_hash:        return Color(0, 128, 128, 255);
        case "navy"_hash:        return Color(0, 0, 128, 255);
        case "purple"_hash:      return Color(128, 0, 128, 255);
        case "orange"_hash:      return Color(255, 165, 0, 255);
        default:                 return std::nullopt;
    }
}

static bool parse_css_func_args(std::string_view sv, double out_vals[4], size_t& count) noexcept {
    count = 0;
    while (!sv.empty() && count < 4) {
        sv = trim_view(sv);
        if (sv.empty()) break;
        size_t comma = sv.find(',');
        std::string_view token = (comma != std::string_view::npos) ? sv.substr(0, comma) : sv;
        if (comma != std::string_view::npos) {
            sv = sv.substr(comma + 1);
        } else {
            sv = {};
        }
        token = trim_view(token);
        if (!token.empty() && token.back() == '%') {
            token.remove_suffix(1);
        }
        out_vals[count++] = fast_parse_double(token, 0.0);
    }
    return count >= 3;
}

} // anonymous namespace

StyleEngine& StyleEngine::instance() {
    static StyleEngine engine;
    return engine;
}

StyleEngine::StyleEngine() {
    init_default_themes();
}

void StyleEngine::init_default_themes() {
    // Rules are stored per theme; resolve() falls back to "dark" rules for
    // themes that do not register their own element rules.
    register_theme("dark", DEFAULT_DARK_THEME_CSS);
    register_theme("light", DEFAULT_LIGHT_THEME_CSS);
}


uint32_t StyleEngine::intern_token(const std::string& token) {
    auto it = token_to_id_.find(token);
    if (it != token_to_id_.end()) {
        return it->second;
    }
    uint32_t id = next_token_id_++;
    token_to_id_[token] = id;
    if (id_to_token_.size() <= id) {
        id_to_token_.resize(id + 1);
    }
    id_to_token_[id] = token;
    return id;
}

void StyleEngine::register_theme(const std::string& theme_name, const std::string& css_text) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    theme_stylesheets_[theme_name] = css_text;
    parse_and_apply_css(css_text, theme_name);
    resolve_cache_.clear();
    ++revision_;
}

void StyleEngine::set_theme(const std::string& theme_name) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    current_theme_ = theme_name;
    resolve_cache_.clear();
    ++revision_;
}

std::string StyleEngine::get_theme() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    return current_theme_;
}

std::vector<std::string> StyleEngine::get_available_themes() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    std::vector<std::string> names;
    for (const auto& [name, _] : theme_stylesheets_) {
        names.push_back(name);
    }
    return names;
}

void StyleEngine::load_stylesheet(const std::string& css_text) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    parse_and_apply_css(css_text, "");
    resolve_cache_.clear();
    ++revision_;
}

void StyleEngine::set_variable(const std::string& key, const std::string& value, const std::string& theme_name) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    uint32_t id = intern_token(key);
    std::string eff_theme = theme_name.empty() ? current_theme_ : theme_name;
    theme_variables_[eff_theme][id] = value;
    resolve_cache_.clear();
    ++revision_;
}

std::string StyleEngine::get_variable(const std::string& key, const std::string& theme_name) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    auto it_t = token_to_id_.find(key);
    if (it_t == token_to_id_.end()) return "";
    uint32_t id = it_t->second;

    std::string eff_theme = theme_name.empty() ? current_theme_ : theme_name;
    auto it_theme = theme_variables_.find(eff_theme);
    if (it_theme != theme_variables_.end()) {
        auto it_var = it_theme->second.find(id);
        if (it_var != it_theme->second.end()) {
            return it_var->second;
        }
    }

    // Fallback to "dark" theme variables if not found
    auto it_dark = theme_variables_.find("dark");
    if (it_dark != theme_variables_.end()) {
        auto it_var = it_dark->second.find(id);
        if (it_var != it_dark->second.end()) {
            return it_var->second;
        }
    }
    return "";
}

std::unordered_map<std::string, std::string> StyleEngine::get_all_variables(const std::string& theme_name) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    std::unordered_map<std::string, std::string> result;
    std::string eff_theme = theme_name.empty() ? current_theme_ : theme_name;

    // Start with dark theme defaults if not already dark
    if (eff_theme != "dark") {
        auto it_dark = theme_variables_.find("dark");
        if (it_dark != theme_variables_.end()) {
            for (const auto& [id, raw_val] : it_dark->second) {
                if (id < id_to_token_.size()) {
                    result[id_to_token_[id]] = resolve_var_string(raw_val, 0, eff_theme);
                }
            }
        }
    }

    auto it_theme = theme_variables_.find(eff_theme);
    if (it_theme != theme_variables_.end()) {
        for (const auto& [id, raw_val] : it_theme->second) {
            if (id < id_to_token_.size()) {
                result[id_to_token_[id]] = resolve_var_string(raw_val, 0, eff_theme);
            }
        }
    }
    return result;
}

std::string StyleEngine::resolve_var_string(const std::string& val, int depth, const std::string& theme_name) const {
    // Guard against cyclic references (e.g. --a: var(--a)): beyond the depth
    // limit the expression resolves to nothing instead of echoing var(...).
    if (depth > 8) return "";
    std::string s = trim(val);
    size_t search_from = 0;
    for (int iter = 0; iter < 64; ++iter) {
        size_t var_pos = s.find("var(", search_from);
        if (var_pos == std::string::npos) break;

        // Find the matching close paren, honouring nested parentheses.
        size_t i = var_pos + 4;
        int paren_depth = 1;
        while (i < s.size() && paren_depth > 0) {
            if (s[i] == '(') ++paren_depth;
            else if (s[i] == ')') --paren_depth;
            ++i;
        }
        if (paren_depth != 0) break;
        size_t close_pos = i - 1;

        std::string inner = s.substr(var_pos + 4, close_pos - (var_pos + 4));
        std::string var_name;
        std::string fallback;
        size_t comma_pos = inner.find(',');
        if (comma_pos != std::string::npos) {
            var_name = trim(inner.substr(0, comma_pos));
            fallback = trim(inner.substr(comma_pos + 1));
        } else {
            var_name = trim(inner);
        }

        std::string resolved = get_variable(var_name, theme_name);
        if (resolved.empty()) {
            resolved = fallback;
        }
        if (!resolved.empty()) {
            resolved = resolve_var_string(resolved, depth + 1, theme_name);
        }

        s.replace(var_pos, close_pos - var_pos + 1, resolved);
        search_from = var_pos + resolved.size();
    }
    return s;
}

Color StyleEngine::resolve_color(const std::string& color_str, const std::string& theme_name) const {
    if (color_str.empty()) return Color(0, 0, 0, 0);

    // Fast-path: hex color literal without var(...)
    if (color_str.front() == '#' && color_str.find("var(") == std::string::npos) {
        return Color::from_hex(color_str);
    }

    std::string s = resolve_var_string(color_str, 0, theme_name);
    std::string_view sv = trim_view(s);
    if (sv.empty()) return Color(0, 0, 0, 0);

    // Hex format
    if (sv.front() == '#') {
        return Color::from_hex(sv);
    }

    // Named color via compile-time FNV-1a switch
    auto named = match_named_color(sv);
    if (named.has_value()) return *named;

    // rgb(...) / rgba(...)
    if (sv.starts_with("rgb(") || sv.starts_with("rgba(")) {
        size_t open_p = sv.find('(');
        size_t close_p = sv.rfind(')');
        if (open_p != std::string_view::npos && close_p != std::string_view::npos && close_p > open_p) {
            double vals[4]{0};
            size_t count = 0;
            if (parse_css_func_args(sv.substr(open_p + 1, close_p - open_p - 1), vals, count)) {
                uint8_t r = static_cast<uint8_t>(std::clamp(vals[0], 0.0, 255.0));
                uint8_t g = static_cast<uint8_t>(std::clamp(vals[1], 0.0, 255.0));
                uint8_t b = static_cast<uint8_t>(std::clamp(vals[2], 0.0, 255.0));
                uint8_t a = 255;
                if (count >= 4) {
                    double a_val = vals[3];
                    if (a_val <= 1.0) a_val *= 255.0;
                    a = static_cast<uint8_t>(std::clamp(a_val + 0.5, 0.0, 255.0));
                }
                return Color(r, g, b, a);
            }
        }
    }

    // hsl(...) / hsla(...)
    if (sv.starts_with("hsl(") || sv.starts_with("hsla(")) {
        size_t open_p = sv.find('(');
        size_t close_p = sv.rfind(')');
        if (open_p != std::string_view::npos && close_p != std::string_view::npos && close_p > open_p) {
            double vals[4]{0};
            size_t count = 0;
            if (parse_css_func_args(sv.substr(open_p + 1, close_p - open_p - 1), vals, count)) {
                double h = vals[0];
                double sl = vals[1] / 100.0;
                double l = vals[2] / 100.0;
                double a = 1.0;
                if (count >= 4) a = (vals[3] <= 1.0) ? vals[3] : vals[3] / 100.0;
                return hsl_to_color(h, sl, l, a);
            }
        }
    }

    // Check if it's an interned variable name or token directly (e.g. "primary", "card_bg")
    std::string token_val = get_variable("--" + s, theme_name);
    if (!token_val.empty()) {
        return resolve_color(token_val, theme_name);
    }
    std::string token_val2 = get_variable(s, theme_name);
    if (!token_val2.empty()) {
        return resolve_color(token_val2, theme_name);
    }

    return Color(0, 0, 0, 0);
}

Color StyleEngine::resolve_color_var(const std::string& val, const Color& fallback, const std::string& theme_name) const {
    if (val.empty()) return fallback;
    if (val.rfind("--", 0) == 0) {
        std::string v = get_variable(val, theme_name);
        if (!v.empty()) {
            return resolve_color_var(v, fallback, theme_name);
        }
        // Semantic component variable fallbacks via compile-time FNV-1a switch
        switch (fnv1a64(val)) {
            case "--btn-hover-bg"_hash:
            case "--btn-active-bg"_hash:
            case "--btn-disabled-bg"_hash: {
                std::string base = get_variable("--btn-bg", theme_name);
                if (base.empty()) base = get_variable("--card-bg", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--btn-hover-fg"_hash:
            case "--btn-active-fg"_hash:
            case "--btn-disabled-fg"_hash: {
                std::string base = get_variable("--btn-fg", theme_name);
                if (base.empty()) base = get_variable("--fg", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--card-shadow"_hash:
            case "--btn-shadow"_hash: {
                std::string base = get_variable("--shadow", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--box-bg"_hash:
            case "--radio-bg"_hash: {
                std::string base = get_variable("--card-bg", theme_name);
                if (base.empty()) base = get_variable("--surface", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--box-border"_hash:
            case "--radio-border"_hash: {
                std::string base = get_variable("--card-border", theme_name);
                if (base.empty()) base = get_variable("--input-border", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--active-bg"_hash:
            case "--active-track-bg"_hash:
            case "--bar-bg"_hash:
            case "--dot-color"_hash: {
                std::string base = get_variable("--primary", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--check-color"_hash: {
                std::string base = get_variable("--primary-fg", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--thumb-bg"_hash:
            case "--thumb-active-bg"_hash: {
                std::string base = get_variable("--thumb-color", theme_name);
                if (base.empty()) base = get_variable("--primary", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--badge-bg"_hash: {
                std::string base = get_variable("--surface", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--badge-fg"_hash: {
                std::string base = get_variable("--fg", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            case "--focus-ring-color"_hash: {
                std::string base = get_variable("--primary", theme_name);
                if (!base.empty()) return resolve_color_var(base, fallback, theme_name);
                break;
            }
            default:
                break;
        }
        return fallback;
    }
    std::string s = resolve_var_string(val, 0, theme_name);
    s = trim(s);
    if (s.empty()) return fallback;
    Color c = resolve_color(s, theme_name);
    if (c.a == 0 && c.r == 0 && c.g == 0 && c.b == 0) {
        switch (fnv1a64_lower(trim_view(s))) {
            case "transparent"_hash:
            case "none"_hash:
            case "#00000000"_hash:
            case "#0000"_hash:
            case "rgba(0,0,0,0)"_hash:
            case "rgba(0, 0, 0, 0)"_hash:
                break;
            default:
                return fallback;
        }
    }
    return c;
}

Color StyleEngine::get_contrast_color(const Color& bg, const Color& light_fg, const Color& dark_fg) const {
    return bg.get_contrast_color(light_fg, dark_fg);
}

double StyleEngine::resolve_scalar(const std::string& val, double fallback, const std::string& theme_name) const {
    if (val.empty()) return fallback;
    if (val.rfind("--", 0) == 0) {
        std::string v = get_variable(val, theme_name);
        if (!v.empty()) return resolve_scalar(v, fallback, theme_name);
        return fallback;
    }
    if (val.find("var(") == std::string::npos) {
        try {
            size_t idx = 0;
            double v = std::stod(val, &idx);
            return v;
        } catch (...) {}
    }
    std::string s = resolve_var_string(val, 0, theme_name);
    s = trim(s);
    if (s.empty()) return fallback;
    try {
        size_t idx = 0;
        double v = std::stod(s, &idx);
        return v;
    } catch (...) {
        return fallback;
    }
}

std::string StyleEngine::resolve_string(const std::string& val, const std::string& fallback, const std::string& theme_name) const {
    if (val.empty()) return fallback;
    if (val.rfind("--", 0) == 0) {
        std::string v = get_variable(val, theme_name);
        if (!v.empty()) return resolve_string(v, fallback, theme_name);
        return fallback;
    }
    std::string s = resolve_var_string(val, 0, theme_name);
    s = trim(s);
    if (s.empty()) return fallback;
    return strip_quotes(s);
}

void StyleEngine::clear_cache() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    resolve_cache_.clear();
}

void StyleEngine::parse_and_apply_css(const std::string& css_text, const std::string& target_theme) {
    // Named themes own their rules (re-registering replaces them);
    // unnamed stylesheets append to the shared base rules.
    std::vector<StyleRule>& out_rules = target_theme.empty() ? base_rules_ : theme_rules_[target_theme];
    if (!target_theme.empty()) out_rules.clear();

    // 1. Remove comments
    std::string clean;
    clean.reserve(css_text.size());
    size_t i = 0;
    while (i < css_text.size()) {
        if (i + 1 < css_text.size() && css_text[i] == '/' && css_text[i + 1] == '*') {
            size_t end_comment = css_text.find("*/", i + 2);
            if (end_comment == std::string::npos) break;
            i = end_comment + 2;
        } else {
            clean.push_back(css_text[i]);
            ++i;
        }
    }

    // 2. Parse rule blocks
    size_t pos = 0;
    while (pos < clean.size()) {
        size_t open_brace = clean.find('{', pos);
        if (open_brace == std::string::npos) break;

        // Find the matching close brace so nested blocks (@media etc.) are skipped whole.
        size_t close_brace = std::string::npos;
        int brace_depth = 1;
        for (size_t k = open_brace + 1; k < clean.size(); ++k) {
            if (clean[k] == '{') ++brace_depth;
            else if (clean[k] == '}' && --brace_depth == 0) {
                close_brace = k;
                break;
            }
        }
        if (close_brace == std::string::npos) break;

        std::string selector_group = trim(clean.substr(pos, open_brace - pos));
        std::string body = clean.substr(open_brace + 1, close_brace - open_brace - 1);
        pos = close_brace + 1;

        if (selector_group.empty()) continue;
        if (selector_group.front() == '@') continue; // unsupported at-rule

        // Parse declarations (source order preserved)
        std::vector<StyleDeclaration> decls;
        for (const std::string& raw_item : split_top_level(body, ';')) {
            std::string item = trim(raw_item);
            if (item.empty()) continue;
            size_t colon = item.find(':');
            if (colon == std::string::npos) continue;
            std::string prop = trim(item.substr(0, colon));
            std::string val = trim(item.substr(colon + 1));
            static const std::string kImportant = "!important";
            if (val.size() >= kImportant.size() &&
                to_lower(val.substr(val.size() - kImportant.size())) == kImportant) {
                val = trim(val.substr(0, val.size() - kImportant.size()));
            }
            if (!prop.empty() && !val.empty()) {
                CssProperty cp = parse_css_property(prop);
                decls.push_back(StyleDeclaration{cp, std::move(prop), std::move(val)});
            }
        }

        // Split multiple comma-separated selectors
        for (const std::string& raw_sel : split_top_level(selector_group, ',')) {
            std::string single_sel = trim(raw_sel);
            if (single_sel.empty()) continue;

            if (single_sel == ":root") {
                // Store custom properties into target_theme variables
                std::string theme_key = target_theme.empty() ? current_theme_ : target_theme;
                for (const auto& decl : decls) {
                    if (decl.name.rfind("--", 0) == 0) {
                        uint32_t id = intern_token(decl.name);
                        theme_variables_[theme_key][id] = decl.value;
                        // Also store under alias without dashes if helpful
                        std::string alias = decl.name.substr(2);
                        theme_variables_[theme_key][intern_token(alias)] = decl.value;
                    }
                }
                continue;
            }

            StyleRule rule;
            rule.declarations = decls;

            // Parse selector components: element, .class, :pseudo
            std::string sel = single_sel;
            
            // Check pseudo-class via compile-time FNV-1a switch
            size_t pseudo_pos = sel.find(':');
            if (pseudo_pos != std::string::npos) {
                std::string pseudo = sel.substr(pseudo_pos + 1);
                sel = sel.substr(0, pseudo_pos);
                switch (fnv1a64_lower(trim_view(pseudo))) {
                    case "hover"_hash:
                        rule.pseudo_state |= PseudoState::Hover;
                        break;
                    case "active"_hash:
                        rule.pseudo_state |= PseudoState::Active;
                        break;
                    case "focus"_hash:
                    case "focused"_hash:
                        rule.pseudo_state |= PseudoState::Focused;
                        break;
                    case "disabled"_hash:
                        rule.pseudo_state |= PseudoState::Disabled;
                        break;
                    case "checked"_hash:
                        rule.pseudo_state |= PseudoState::Checked;
                        break;
                    default:
                        break;
                }
                rule.specificity += 100;
            }

            // Check class
            size_t dot_pos = sel.find('.');
            if (dot_pos != std::string::npos) {
                rule.class_name = to_lower(sel.substr(dot_pos + 1));
                rule.element = to_lower(sel.substr(0, dot_pos));
                rule.specificity += 10;
                if (!rule.element.empty()) {
                    rule.specificity += 1;
                }
            } else {
                rule.element = to_lower(sel);
                if (!rule.element.empty() && rule.element != "*") {
                    rule.specificity += 1;
                }
            }

            out_rules.push_back(rule);
        }
    }
}

ComputedStyle StyleEngine::resolve(
    const std::string& element,
    const std::string& class_name,
    uint16_t states
) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);

    // 1. Check $O(1)$ resolution cache
    std::string eff_el = to_lower(element);
    std::string eff_cls = to_lower(class_name);
    // Strip leading dot if provided
    if (!eff_cls.empty() && eff_cls.front() == '.') {
        eff_cls.erase(0, 1);
    }

    // Exact composite key (no hash collisions possible)
    std::string cache_key;
    cache_key.reserve(current_theme_.size() + eff_el.size() + eff_cls.size() + 8);
    cache_key += current_theme_;
    cache_key += '\x1f';
    cache_key += eff_el;
    cache_key += '\x1f';
    cache_key += eff_cls;
    cache_key += '\x1f';
    cache_key += std::to_string(states);

    auto it_cache = resolve_cache_.find(cache_key);
    if (it_cache != resolve_cache_.end()) {
        return it_cache->second;
    }

    ComputedStyle cs;

    // Collect and sort matching rules by specificity
    struct Match {
        const StyleRule* rule;
        size_t order;
    };
    std::vector<Match> matches;

    // Rule set: current theme's rules (falling back to "dark"), then shared
    // base rules so user stylesheets win ties on specificity.
    std::vector<const StyleRule*> all_rules;
    auto it_rules = theme_rules_.find(current_theme_);
    if (it_rules == theme_rules_.end()) it_rules = theme_rules_.find("dark");
    if (it_rules != theme_rules_.end()) {
        for (const auto& tr : it_rules->second) all_rules.push_back(&tr);
    }
    for (const auto& br : base_rules_) all_rules.push_back(&br);

    for (size_t r_idx = 0; r_idx < all_rules.size(); ++r_idx) {
        const auto& r = *all_rules[r_idx];

        // Pseudo state matching:
        // If rule specifies pseudo states, all of them must be set in 'states'
        if (r.pseudo_state != 0) {
            if ((states & r.pseudo_state) != r.pseudo_state) {
                continue;
            }
        }

        // Element matching
        bool el_match = r.element.empty() || r.element == "*" || r.element == eff_el;
        if (!r.element.empty() && r.element != "*" && r.element != eff_el) {
            // Also allow matching if element name matches class_name or one of the class tokens
            if (r.element == eff_cls) {
                el_match = true;
            } else {
                std::stringstream el_ss(eff_cls);
                std::string c_tok;
                bool found_el = false;
                while (el_ss >> c_tok) {
                    if (!c_tok.empty() && c_tok.front() == '.') c_tok.erase(0, 1);
                    if (r.element == c_tok) {
                        found_el = true;
                        break;
                    }
                }
                el_match = found_el;
            }
        }

        // Class matching
        bool cls_match = true;
        if (!r.class_name.empty()) {
            if (eff_cls.empty()) {
                cls_match = false;
            } else if (r.class_name == eff_cls || r.class_name == "btn-" + eff_cls || r.class_name == "badge-" + eff_cls) {
                cls_match = true;
            } else {
                // Check space-separated class tokens
                bool found = false;
                std::stringstream cls_ss(eff_cls);
                std::string c_tok;
                while (cls_ss >> c_tok) {
                    if (!c_tok.empty() && c_tok.front() == '.') c_tok.erase(0, 1);
                    if (r.class_name == c_tok || r.class_name == "btn-" + c_tok || r.class_name == "badge-" + c_tok) {
                        found = true;
                        break;
                    }
                }
                cls_match = found;
            }
        }

        if (el_match && cls_match) {
            matches.push_back(Match{&r, r_idx});
        }
    }

    std::sort(matches.begin(), matches.end(), [](const Match& a, const Match& b) {
        if (a.rule->specificity != b.rule->specificity) {
            return a.rule->specificity < b.rule->specificity;
        }
        return a.order < b.order;
    });

    // Apply matched declarations in order
    for (const auto& m : matches) {
        for (const auto& decl : m.rule->declarations) {
            switch (decl.property) {
                case CssProperty::BgColor:
                    cs.bg_color = resolve_color(decl.value);
                    break;
                case CssProperty::FgColor:
                    cs.fg_color = resolve_color(decl.value);
                    break;
                case CssProperty::BorderColor:
                    cs.border_color = resolve_color(decl.value);
                    break;
                case CssProperty::BorderWidth:
                    cs.border_width = fast_parse_length(decl.value);
                    break;
                case CssProperty::BorderRadius:
                    cs.border_radius = fast_parse_length(decl.value);
                    break;
                case CssProperty::Border: {
                    std::string_view b_sv = trim_view(decl.value);
                    if (b_sv == "none" || b_sv == "0" || b_sv == "0px") {
                        cs.border_width = 0.0f;
                        cs.border_color = Color(0, 0, 0, 0);
                    } else {
                        std::stringstream b_ss(decl.value);
                        std::string token;
                        while (b_ss >> token) {
                            token = trim(token);
                            if (token.empty()) continue;
                            if (std::isdigit(static_cast<unsigned char>(token.front())) || token.front() == '.') {
                                cs.border_width = fast_parse_length(token);
                            } else if (token == "solid" || token == "dashed" || token == "dotted") {
                                // style indicator
                            } else {
                                std::string rest = token;
                                std::string next;
                                while (b_ss >> next) {
                                    rest += " " + next;
                                }
                                cs.border_color = resolve_color(rest);
                                break;
                            }
                        }
                    }
                    break;
                }
                case CssProperty::BoxShadow: {
                    std::string_view s_sv = trim_view(decl.value);
                    if (s_sv == "none" || s_sv == "0" || s_sv == "0px") {
                        cs.shadow_blur = 0.0f;
                        cs.shadow_offset_x = 0.0f;
                        cs.shadow_offset_y = 0.0f;
                        cs.shadow_color = Color(0, 0, 0, 0);
                    } else {
                        std::stringstream s_ss(decl.value);
                        std::vector<std::string> tokens;
                        std::string t;
                        while (s_ss >> t) {
                            tokens.push_back(t);
                        }
                        if (tokens.size() >= 3) {
                            cs.shadow_offset_x = fast_parse_length(tokens[0]);
                            cs.shadow_offset_y = fast_parse_length(tokens[1]);
                            cs.shadow_blur = fast_parse_length(tokens[2]);

                            size_t color_idx = 3;
                            auto is_num_start = [](char ch) {
                                return std::isdigit(static_cast<unsigned char>(ch)) || ch == '-' || ch == '.';
                            };
                            if (tokens.size() >= 4 && is_num_start(tokens[3].front())) {
                                // 4th token is spread radius
                                color_idx = 4;
                            }

                            std::string col_part;
                            for (size_t k = color_idx; k < tokens.size(); ++k) {
                                if (!col_part.empty()) col_part += " ";
                                col_part += tokens[k];
                            }
                            if (!col_part.empty()) {
                                cs.shadow_color = resolve_color(col_part);
                            }
                        }
                    }
                    break;
                }
                case CssProperty::ShadowBlur:
                    cs.shadow_blur = fast_parse_length(decl.value);
                    break;
                case CssProperty::ShadowColor:
                    cs.shadow_color = resolve_color(decl.value);
                    break;
                case CssProperty::ShadowOffsetX:
                    cs.shadow_offset_x = fast_parse_length(decl.value);
                    break;
                case CssProperty::ShadowOffsetY:
                    cs.shadow_offset_y = fast_parse_length(decl.value);
                    break;
                case CssProperty::FontSize:
                    cs.font_size = fast_parse_length(decl.value, 13.0f);
                    break;
                case CssProperty::FontFamily:
                    cs.font_family = std::string(strip_quotes_view(decl.value));
                    break;
                case CssProperty::FontWeight: {
                    std::string_view fw = trim_view(decl.value);
                    switch (fnv1a64_lower(fw)) {
                        case "bold"_hash:
                            cs.font_weight = 700;
                            break;
                        case "normal"_hash:
                            cs.font_weight = 400;
                            break;
                        case "medium"_hash:
                            cs.font_weight = 500;
                            break;
                        case "semibold"_hash:
                            cs.font_weight = 600;
                            break;
                        default:
                            cs.font_weight = fast_parse_int(fw, 400);
                            break;
                    }
                    break;
                }
                default:
                    break;
            }
        }
    }

    resolve_cache_[cache_key] = cs;
    if (resolve_cache_.size() > 4096) {
        resolve_cache_.clear(); // Simple bounded cache to prevent unbounded growth
    }
    return cs;
}

void StyleEngine::register_container_window(uintptr_t tkwin_ptr, ContainerLayer layer) {
    if (tkwin_ptr == 0) return;
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    container_windows_[tkwin_ptr] = layer;
}

void StyleEngine::unregister_container_window(uintptr_t tkwin_ptr) {
    if (tkwin_ptr == 0) return;
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    container_windows_.erase(tkwin_ptr);
}

ContainerLayer StyleEngine::resolve_window_layer(uintptr_t tkwin_ptr) const {
    if (tkwin_ptr == 0) return ContainerLayer::Base;
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    auto it = container_windows_.find(tkwin_ptr);
    if (it != container_windows_.end()) {
        return it->second;
    }
    return ContainerLayer::Base;
}

Color StyleEngine::get_layer_color(ContainerLayer layer, const std::string& theme_name) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    std::string t_name = theme_name.empty() ? current_theme_ : theme_name;
    switch (layer) {
        case ContainerLayer::Base:
            return resolve_color_var("--bg", Color(16, 14, 20, 255), t_name);
        case ContainerLayer::Surface: {
            Color c = resolve_color_var("--surface", Color(0, 0, 0, 0), t_name);
            if (c.a == 0 && c.r == 0 && c.g == 0 && c.b == 0) {
                c = resolve_color_var("--card-bg", Color(29, 27, 32, 255), t_name);
            }
            return c;
        }
        case ContainerLayer::Elevated: {
            Color c = resolve_color_var("--surface-elevated", Color(0, 0, 0, 0), t_name);
            if (c.a == 0 && c.r == 0 && c.g == 0 && c.b == 0) {
                c = resolve_color_var("--card-bg", Color(37, 35, 42, 255), t_name);
            }
            return c;
        }
        default:
            return resolve_color_var("--bg", Color(16, 14, 20, 255), t_name);
    }
}

void StyleEngine::register_element_batch(const std::string& element, const DrawBatch& batch) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    element_batches_[to_lower(trim(element))] = batch;
}

const DrawBatch* StyleEngine::get_element_batch(const std::string& element) const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    auto it = element_batches_.find(to_lower(trim(element)));
    if (it != element_batches_.end()) {
        return &it->second;
    }
    return nullptr;
}

} // namespace tkblend
