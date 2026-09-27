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

} // anonymous namespace

StyleEngine& StyleEngine::instance() {
    static StyleEngine engine;
    return engine;
}

StyleEngine::StyleEngine() {
    init_default_themes();
}

void StyleEngine::init_default_themes() {
    register_theme("dark", DEFAULT_DARK_THEME_CSS);
    register_theme("light", DEFAULT_LIGHT_THEME_CSS);

    // Global widget rules fallback
    parse_and_apply_css(DEFAULT_DARK_THEME_CSS, "");
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
}

void StyleEngine::set_theme(const std::string& theme_name) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    current_theme_ = theme_name;
    resolve_cache_.clear();
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
}

void StyleEngine::set_variable(const std::string& key, const std::string& value, const std::string& theme_name) {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    uint32_t id = intern_token(key);
    std::string eff_theme = theme_name.empty() ? current_theme_ : theme_name;
    theme_variables_[eff_theme][id] = value;
    resolve_cache_.clear();
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

std::string StyleEngine::resolve_var_string(const std::string& val, int depth, const std::string& theme_name) const {
    if (depth > 8) return val;
    std::string s = trim(val);
    size_t var_pos = s.find("var(");
    while (var_pos != std::string::npos) {
        size_t close_pos = s.find(')', var_pos);
        if (close_pos == std::string::npos) break;

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
        var_pos = s.find("var(");
    }
    return s;
}

Color StyleEngine::resolve_color(const std::string& color_str) const {
    std::string s = resolve_var_string(color_str);
    s = trim(s);
    if (s.empty()) return Color(0, 0, 0, 0);

    // Hex format
    if (s.front() == '#') {
        return Color::from_hex(s);
    }

    std::string low = to_lower(s);

    if (low == "transparent") return Color(0, 0, 0, 0);
    if (low == "none") return Color(0, 0, 0, 0);
    if (low == "white") return Color(255, 255, 255, 255);
    if (low == "black") return Color(0, 0, 0, 255);
    if (low == "red") return Color(255, 0, 0, 255);
    if (low == "green") return Color(0, 255, 0, 255);
    if (low == "blue") return Color(0, 0, 255, 255);
    if (low == "yellow") return Color(255, 255, 0, 255);
    if (low == "cyan" || low == "aqua") return Color(0, 255, 255, 255);
    if (low == "magenta") return Color(255, 0, 255, 255);
    if (low == "gray" || low == "grey") return Color(128, 128, 128, 255);
    if (low == "silver") return Color(192, 192, 192, 255);
    if (low == "maroon") return Color(128, 0, 0, 255);
    if (low == "olive") return Color(128, 128, 0, 255);
    if (low == "lime") return Color(0, 255, 0, 255);
    if (low == "teal") return Color(0, 128, 128, 255);
    if (low == "navy") return Color(0, 0, 128, 255);
    if (low == "purple") return Color(128, 0, 128, 255);
    if (low == "orange") return Color(255, 165, 0, 255);

    // rgb(...) / rgba(...)
    if (low.rfind("rgb", 0) == 0) {
        size_t open_p = low.find('(');
        size_t close_p = low.rfind(')');
        if (open_p != std::string::npos && close_p != std::string::npos && close_p > open_p) {
            std::string args = low.substr(open_p + 1, close_p - open_p - 1);
            std::stringstream ss(args);
            std::string item;
            std::vector<double> vals;
            while (std::getline(ss, item, ',')) {
                item = trim(item);
                if (item.empty()) continue;
                try {
                    vals.push_back(std::stod(item));
                } catch (...) {}
            }
            if (vals.size() >= 3) {
                uint8_t r = static_cast<uint8_t>(std::clamp(vals[0], 0.0, 255.0));
                uint8_t g = static_cast<uint8_t>(std::clamp(vals[1], 0.0, 255.0));
                uint8_t b = static_cast<uint8_t>(std::clamp(vals[2], 0.0, 255.0));
                uint8_t a = 255;
                if (vals.size() >= 4) {
                    double a_val = vals[3];
                    if (a_val <= 1.0) a_val *= 255.0;
                    a = static_cast<uint8_t>(std::clamp(a_val + 0.5, 0.0, 255.0));
                }
                return Color(r, g, b, a);
            }
        }
    }

    // hsl(...) / hsla(...)
    if (low.rfind("hsl", 0) == 0) {
        size_t open_p = low.find('(');
        size_t close_p = low.rfind(')');
        if (open_p != std::string::npos && close_p != std::string::npos && close_p > open_p) {
            std::string args = low.substr(open_p + 1, close_p - open_p - 1);
            std::stringstream ss(args);
            std::string item;
            std::vector<double> vals;
            while (std::getline(ss, item, ',')) {
                item = trim(item);
                if (item.empty()) continue;
                if (!item.empty() && item.back() == '%') item.pop_back();
                try {
                    vals.push_back(std::stod(item));
                } catch (...) {}
            }
            if (vals.size() >= 3) {
                double h = vals[0];
                double s = vals[1] / 100.0;
                double l = vals[2] / 100.0;
                double a = 1.0;
                if (vals.size() >= 4) a = vals[3] <= 1.0 ? vals[3] : vals[3] / 100.0;
                return hsl_to_color(h, s, l, a);
            }
        }
    }

    // Check if it's an interned variable name or token directly (e.g. "primary", "card_bg")
    std::string token_val = get_variable("--" + s);
    if (!token_val.empty()) {
        return resolve_color(token_val);
    }
    std::string token_val2 = get_variable(s);
    if (!token_val2.empty()) {
        return resolve_color(token_val2);
    }

    return Color(0, 0, 0, 255);
}

void StyleEngine::clear_cache() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    resolve_cache_.clear();
}

void StyleEngine::parse_and_apply_css(const std::string& css_text, const std::string& target_theme) {
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
        size_t close_brace = clean.find('}', open_brace + 1);
        if (close_brace == std::string::npos) break;

        std::string selector_group = trim(clean.substr(pos, open_brace - pos));
        std::string body = clean.substr(open_brace + 1, close_brace - open_brace - 1);
        pos = close_brace + 1;

        if (selector_group.empty()) continue;

        // Parse declarations
        std::unordered_map<std::string, std::string> decls;
        std::stringstream ss(body);
        std::string item;
        while (std::getline(ss, item, ';')) {
            item = trim(item);
            if (item.empty()) continue;
            size_t colon = item.find(':');
            if (colon == std::string::npos) continue;
            std::string prop = trim(item.substr(0, colon));
            std::string val = trim(item.substr(colon + 1));
            if (!prop.empty() && !val.empty()) {
                decls[to_lower(prop)] = val;
            }
        }

        // Split multiple comma-separated selectors
        std::stringstream sel_ss(selector_group);
        std::string single_sel;
        while (std::getline(sel_ss, single_sel, ',')) {
            single_sel = trim(single_sel);
            if (single_sel.empty()) continue;

            if (single_sel == ":root") {
                // Store custom properties into target_theme variables
                std::string theme_key = target_theme.empty() ? current_theme_ : target_theme;
                for (const auto& [prop, val] : decls) {
                    if (prop.rfind("--", 0) == 0) {
                        uint32_t id = intern_token(prop);
                        theme_variables_[theme_key][id] = val;
                        // Also store under alias without dashes if helpful
                        std::string alias = prop.substr(2);
                        theme_variables_[theme_key][intern_token(alias)] = val;
                    }
                }
                continue;
            }

            StyleRule rule;
            rule.declarations = decls;

            // Parse selector components: element, .class, :pseudo
            std::string sel = single_sel;
            
            // Check pseudo-class
            size_t pseudo_pos = sel.find(':');
            if (pseudo_pos != std::string::npos) {
                std::string pseudo = to_lower(sel.substr(pseudo_pos + 1));
                sel = sel.substr(0, pseudo_pos);
                if (pseudo == "hover") {
                    rule.pseudo_state |= PseudoState::Hover;
                } else if (pseudo == "active") {
                    rule.pseudo_state |= PseudoState::Active;
                } else if (pseudo == "focus" || pseudo == "focused") {
                    rule.pseudo_state |= PseudoState::Focused;
                } else if (pseudo == "disabled") {
                    rule.pseudo_state |= PseudoState::Disabled;
                } else if (pseudo == "checked") {
                    rule.pseudo_state |= PseudoState::Checked;
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

            global_rules_.push_back(rule);
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

    uint64_t h_el = std::hash<std::string>()(eff_el);
    uint64_t h_cls = std::hash<std::string>()(eff_cls);
    uint64_t h_th = std::hash<std::string>()(current_theme_);
    uint64_t key_hash = h_el ^ (h_cls << 16) ^ (static_cast<uint64_t>(states) << 32) ^ (h_th << 48);

    auto it_cache = resolve_cache_.find(key_hash);
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

    for (size_t r_idx = 0; r_idx < global_rules_.size(); ++r_idx) {
        const auto& r = global_rules_[r_idx];

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
            // Also allow matching if element name matches class_name (e.g. .card widget tag)
            if (r.element != eff_cls) {
                el_match = false;
            } else {
                el_match = true;
            }
        }

        // Class matching
        bool cls_match = true;
        if (!r.class_name.empty()) {
            if (eff_cls.empty()) {
                cls_match = false;
            } else if (r.class_name != eff_cls) {
                // Check prefix e.g. .btn-primary matching "primary"
                if (r.class_name == "btn-" + eff_cls || r.class_name == "badge-" + eff_cls) {
                    cls_match = true;
                } else {
                    cls_match = false;
                }
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
        for (const auto& [prop, val] : m.rule->declarations) {
            if (prop == "background" || prop == "background-color" || prop == "bg") {
                cs.bg_color = resolve_color(val);
            } else if (prop == "color" || prop == "foreground" || prop == "fg") {
                cs.fg_color = resolve_color(val);
            } else if (prop == "border-color") {
                cs.border_color = resolve_color(val);
            } else if (prop == "border-width") {
                cs.border_width = parse_length(val);
            } else if (prop == "border-radius" || prop == "radius" || prop == "rx" || prop == "ry") {
                cs.border_radius = parse_length(val);
            } else if (prop == "border") {
                std::string b_str = trim(val);
                if (b_str == "none" || b_str == "0" || b_str == "0px") {
                    cs.border_width = 0.0f;
                    cs.border_color = Color(0, 0, 0, 0);
                } else {
                    std::stringstream b_ss(b_str);
                    std::string token;
                    while (b_ss >> token) {
                        token = trim(token);
                        if (token.empty()) continue;
                        if (std::isdigit(token.front()) || token.front() == '.') {
                            cs.border_width = parse_length(token);
                        } else if (token == "solid" || token == "dashed" || token == "dotted") {
                            // style indicator
                        } else {
                            // Color token or var(...)
                            // If rest of string has var or rgba, read rest
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
            } else if (prop == "box-shadow") {
                std::string s_str = trim(val);
                if (s_str == "none" || s_str == "0" || s_str == "0px") {
                    cs.shadow_blur = 0.0f;
                    cs.shadow_offset_x = 0.0f;
                    cs.shadow_offset_y = 0.0f;
                    cs.shadow_color = Color(0, 0, 0, 0);
                } else {
                    std::stringstream s_ss(s_str);
                    std::vector<std::string> tokens;
                    std::string t;
                    while (s_ss >> t) {
                        tokens.push_back(t);
                    }
                    if (tokens.size() >= 3) {
                        cs.shadow_offset_x = parse_length(tokens[0]);
                        cs.shadow_offset_y = parse_length(tokens[1]);
                        cs.shadow_blur = parse_length(tokens[2]);

                        size_t color_idx = 3;
                        if (tokens.size() >= 4 && (std::isdigit(tokens[3].front()) || tokens[3].front() == '-' || tokens[3].front() == '.')) {
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
            } else if (prop == "shadow-blur") {
                cs.shadow_blur = parse_length(val);
            } else if (prop == "shadow-color") {
                cs.shadow_color = resolve_color(val);
            } else if (prop == "shadow-offset-x") {
                cs.shadow_offset_x = parse_length(val);
            } else if (prop == "shadow-offset-y") {
                cs.shadow_offset_y = parse_length(val);
            } else if (prop == "font-size") {
                cs.font_size = parse_length(val);
            } else if (prop == "font-family") {
                cs.font_family = strip_quotes(val);
            } else if (prop == "font-weight") {
                std::string fw = to_lower(trim(val));
                if (fw == "bold") cs.font_weight = 700;
                else if (fw == "normal") cs.font_weight = 400;
                else if (fw == "medium") cs.font_weight = 500;
                else if (fw == "semibold") cs.font_weight = 600;
                else cs.font_weight = static_cast<int>(parse_length(val));
            }
        }
    }

    resolve_cache_[key_hash] = cs;
    return cs;
}

} // namespace tkblend
