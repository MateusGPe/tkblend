#include "draw_engine.hpp"
#include "native_controller.hpp"
#include "style_engine.hpp"
#include "fnv1a.hpp"
#include "string_utils.hpp"
#include <algorithm>
#include <cctype>

namespace tkblend {

namespace {

static inline double resolve_token(
    std::string_view token,
    const std::unordered_map<uint64_t, std::string>& vars,
    double fallback
) {
    uint64_t hash = fnv1a64(extract_var_view(token));
    auto it = vars.find(hash);
    if (it != vars.end() && !it->second.empty()) {
        try {
            size_t idx = 0;
            return std::stod(it->second, &idx);
        } catch (...) {}
    }
    return StyleEngine::instance().resolve_scalar(std::string(token), fallback);
}

static inline std::string resolve_token_str(
    std::string_view token,
    const std::unordered_map<uint64_t, std::string>& vars,
    const std::string& fallback = ""
) {
    uint64_t hash = fnv1a64(extract_var_view(token));
    auto it = vars.find(hash);
    if (it != vars.end() && !it->second.empty()) {
        return it->second;
    }
    return StyleEngine::instance().resolve_string(std::string(token), fallback);
}

static std::string to_lower_trim(const std::string& str) {
    auto start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    auto end = str.find_last_not_of(" \t\n\r");
    std::string res = str.substr(start, end - start + 1);
    std::transform(res.begin(), res.end(), res.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return res;
}

static int count_bits(uint16_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_popcount(val);
#else
    int c = 0;
    while (val) {
        c += (val & 1);
        val >>= 1;
    }
    return c;
#endif
}

} // namespace

DrawEngine& DrawEngine::instance() {
    static DrawEngine inst;
    return inst;
}

DrawEngine::DrawEngine() {
    init_default_batches();
}

void DrawEngine::register_batch(const std::string& widget_class, uint16_t state_mask, const DrawBatch& batch) {
    std::string key_cls = to_lower_trim(widget_class);
    if (key_cls.empty()) return;

    std::lock_guard<std::recursive_mutex> lock(mutex_);
    batches_[Key{key_cls, state_mask}] = batch;
}

void DrawEngine::unregister_batch(const std::string& widget_class, uint16_t state_mask) {
    std::string key_cls = to_lower_trim(widget_class);
    if (key_cls.empty()) return;

    std::lock_guard<std::recursive_mutex> lock(mutex_);
    batches_.erase(Key{key_cls, state_mask});
}

const DrawBatch* DrawEngine::get_batch(const std::string& widget_class, uint16_t state) const {
    std::string key_cls = to_lower_trim(widget_class);
    if (key_cls.empty()) return nullptr;

    std::lock_guard<std::recursive_mutex> lock(mutex_);

    // 1. Exact match
    auto it = batches_.find(Key{key_cls, state});
    if (it != batches_.end()) {
        return &it->second;
    }

    // 2. Best matching registered mask where (state & mask) == mask
    const DrawBatch* best_batch = nullptr;
    int best_popcount = 0;

    for (const auto& [k, batch] : batches_) {
        if (k.widget_class == key_cls && k.state_mask != 0) {
            if ((state & k.state_mask) == k.state_mask) {
                int pop = count_bits(k.state_mask);
                if (pop > best_popcount) {
                    best_popcount = pop;
                    best_batch = &batch;
                }
            }
        }
    }

    if (best_batch) {
        return best_batch;
    }

    // 3. Fallback to default batch (state_mask = 0)
    it = batches_.find(Key{key_cls, 0});
    if (it != batches_.end()) {
        return &it->second;
    }

    return nullptr;
}

bool DrawEngine::has_batch(const std::string& widget_class, uint16_t state) const {
    return get_batch(widget_class, state) != nullptr;
}

DrawBatch DrawEngine::create_control_batch(
    const std::string& widget_class,
    uint16_t state,
    double w,
    double h,
    const std::unordered_map<std::string, std::string>& vars
) const {
    std::unordered_map<uint64_t, std::string> hashed;
    hashed.reserve(vars.size());
    for (const auto& [k, v] : vars) {
        hashed[fnv1a64(extract_var_view(k))] = v;
    }
    return create_control_batch(widget_class, state, w, h, hashed);
}

DrawBatch DrawEngine::create_control_batch(
    const std::string& widget_class,
    uint16_t state,
    double w,
    double h,
    const std::unordered_map<uint64_t, std::string>& vars
) const {
    std::string key_cls = to_lower_trim(widget_class);
    if (key_cls.empty() || w <= 0.0 || h <= 0.0) return DrawBatch();

    DrawBatch b;
    b.clear_var("--parent-bg");

    if (key_cls == "button") {
        double pad_x = resolve_token("--btn-pad-x", vars, 4.0);
        double pad_top = resolve_token("--btn-pad-top", vars, 2.0);
        double pad_bottom = resolve_token("--btn-pad-bottom", vars, 6.0);
        double btn_radius = resolve_token("--btn-radius", vars, 8.0);
        double bx = pad_x;
        double by = pad_top;
        double bw = std::max(4.0, w - 2.0 * pad_x);
        double bh = std::max(4.0, h - pad_top - pad_bottom);
        double press_disp_y = resolve_token("--btn-press-displacement-y", vars, 1.0);

        std::string variant = "";
        auto it_v = vars.find("variant"_hash);
        if (it_v != vars.end()) {
            variant = to_lower_trim(it_v->second);
        }

        std::string bg_var = "--btn-bg";
        std::string fg_var = "--btn-fg";
        std::string border_var = "--btn-border";
        std::string shadow_var = "--btn-shadow";
        double border_w = resolve_token("--btn-border-width", vars, 0.0);
        double shadow_blur = resolve_token("--btn-shadow-blur", vars, 2.0);
        double shadow_off_y = resolve_token("--btn-shadow-y", vars, 0.8);
        Color fallback_bg(37, 35, 42);
        Color fallback_fg(230, 224, 233);
        Color fallback_border(73, 69, 79);
        Color fallback_shadow(0, 0, 0, 28);

        if (variant == "primary") {
            bg_var = "--primary";
            fg_var = "--primary-fg";
            border_var = "--primary";
            border_w = 0.0;
            shadow_blur = 2.2;
            shadow_off_y = 0.8;
            fallback_bg = Color(139, 92, 246);
            fallback_fg = Color(255, 255, 255);
            fallback_border = Color(124, 58, 237);
            fallback_shadow = Color(0, 0, 0, 36);

            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                bg_var = "--btn-disabled-bg";
                fg_var = "--btn-disabled-fg";
                shadow_blur = 0.0;
                shadow_off_y = 0.0;
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                bg_var = "--primary-active";
                shadow_blur = 1.0;
                shadow_off_y = 0.4;
                by += press_disp_y;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                bg_var = "--primary-hover";
                shadow_blur = 3.2;
                shadow_off_y = 1.2;
            }
        } else if (variant == "tonal" || variant == "secondary") {
            bg_var = "--secondary";
            fg_var = "--secondary-fg";
            border_var = "--secondary";
            border_w = 0.0;
            shadow_blur = 1.8;
            shadow_off_y = 0.6;
            fallback_bg = Color(6, 182, 212);
            fallback_fg = Color(255, 255, 255);
            fallback_border = Color(8, 145, 178);

            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                bg_var = "--btn-disabled-bg";
                fg_var = "--btn-disabled-fg";
                shadow_blur = 0.0;
                shadow_off_y = 0.0;
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                bg_var = "--secondary-active";
                shadow_blur = 0.8;
                shadow_off_y = 0.3;
                by += press_disp_y;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                bg_var = "--secondary-hover";
                shadow_blur = 2.6;
                shadow_off_y = 1.0;
            }
        } else if (variant == "outline") {
            bg_var = "--parent-bg";
            fg_var = "--primary";
            border_var = "--btn-border";
            border_w = 1.0;
            shadow_blur = 0.0;
            shadow_off_y = 0.0;
            fallback_bg = Color(0, 0, 0, 0);
            fallback_fg = Color(139, 92, 246);
            fallback_border = Color(73, 69, 79);
            fallback_shadow = Color(0, 0, 0, 0);

            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                fg_var = "--btn-disabled-fg";
                border_var = "--btn-border";
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                bg_var = "--btn-active-bg";
                by += press_disp_y;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                bg_var = "--btn-hover-bg";
                shadow_blur = 1.5;
                shadow_off_y = 0.5;
                fallback_shadow = Color(0, 0, 0, 18);
            }
        } else if (variant == "ghost" || variant == "flat") {
            bg_var = "--parent-bg";
            fg_var = "--primary";
            border_var = "--parent-bg";
            border_w = 0.0;
            shadow_blur = 0.0;
            shadow_off_y = 0.0;
            fallback_bg = Color(0, 0, 0, 0);
            fallback_fg = Color(139, 92, 246);
            fallback_border = Color(0, 0, 0, 0);
            fallback_shadow = Color(0, 0, 0, 0);

            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                fg_var = "--btn-disabled-fg";
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                bg_var = "--btn-active-bg";
                by += press_disp_y;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                bg_var = "--btn-hover-bg";
            }
        } else if (variant == "destructive" || variant == "danger") {
            bg_var = "--destructive";
            fg_var = "#ffffff";
            border_var = "--destructive";
            border_w = 0.0;
            shadow_blur = 2.0;
            shadow_off_y = 0.8;
            fallback_bg = Color(239, 68, 68);
            fallback_fg = Color(255, 255, 255);
            fallback_border = Color(220, 38, 38);
            fallback_shadow = Color(0, 0, 0, 32);

            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                bg_var = "--btn-disabled-bg";
                fg_var = "--btn-disabled-fg";
                shadow_blur = 0.0;
                shadow_off_y = 0.0;
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                by += press_disp_y;
                shadow_blur = 1.0;
                shadow_off_y = 0.4;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                shadow_blur = 3.2;
                shadow_off_y = 1.2;
            }
        } else {
            // Default M3 filled tonal / elevated surface button (borderless)
            border_w = 0.0;
            if ((state & ControllerPseudoState::StateDisabled) != 0) {
                bg_var = "--btn-disabled-bg";
                fg_var = "--btn-disabled-fg";
                shadow_blur = 0.0;
                shadow_off_y = 0.0;
            } else if ((state & ControllerPseudoState::StateActive) != 0) {
                bg_var = "--btn-active-bg";
                fg_var = "--btn-active-fg";
                shadow_blur = 1.0;
                shadow_off_y = 0.4;
                by += press_disp_y;
            } else if ((state & ControllerPseudoState::StateHover) != 0) {
                bg_var = "--btn-hover-bg";
                fg_var = "--btn-hover-fg";
                shadow_blur = resolve_token("--btn-shadow-blur-hover", vars, 2.8);
                shadow_off_y = resolve_token("--btn-shadow-y-hover", vars, 1.0);
            }
        }

        b.draw_card_var(
            bx, by, bw, bh,
            btn_radius, btn_radius,
            bg_var, border_var,
            border_w, shadow_blur, 0.0, 0.0, shadow_off_y,
            shadow_var,
            "--rx", "--ry", "--bw",
            fallback_bg, fallback_border, fallback_shadow
        );

        std::string btn_text = resolve_token_str("--text", vars, "");
        float font_size = static_cast<float>(resolve_token("--btn-font-size", vars, 13.0));
        std::string font_family = resolve_token_str("--btn-font-family", vars, "sans-serif");
        int font_weight = static_cast<int>(resolve_token("--btn-font-weight", vars, 500.0));
        double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);

        std::string anchor = resolve_token_str("--anchor", vars, "center");
        double btn_pad_x = resolve_token("--btn-pad-x", vars, 14.0);
        double text_x = bx + bw / 2.0;
        int align_mode = 1; // center
        if (anchor == "w" || anchor == "left") {
            text_x = bx + btn_pad_x;
            align_mode = 0; // left
        } else if (anchor == "e" || anchor == "right") {
            text_x = bx + bw - btn_pad_x;
            align_mode = 2; // right
        }

        b.draw_text_var(
            btn_text, text_x, by + bh / 2.0 + font_size * baseline_offset, font_size, font_family,
            fg_var, "--text", "--font-size",
            fallback_fg,
            align_mode, font_weight
        );


        if ((state & ControllerPseudoState::StateFocused) != 0) {
            double focus_ring_w = resolve_token("--focus-ring-width", vars, 2.0);
            double focus_ring_pad = resolve_token("--focus-ring-pad", vars, 1.5);
            b.stroke_rounded_rect_var(
                bx - focus_ring_pad, by - focus_ring_pad, bw + 2.0 * focus_ring_pad, bh + 2.0 * focus_ring_pad,
                btn_radius + focus_ring_pad, btn_radius + focus_ring_pad,
                "--focus-ring-color", focus_ring_w,
                "--rx", "--ry", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }
        return b;
    }

    if (key_cls == "switch") {
        std::string sw_text = resolve_token_str("--text", vars, "");
        double focus_pad = resolve_token("--switch-focus-pad", vars, 3.5);
        double track_w = resolve_token("--switch-track-w", vars, 40.0);
        double track_h = resolve_token("--switch-track-h", vars, 22.0);

        if (w > 0.0 && w < track_w + 2.0 * focus_pad) {
            track_w = std::max(12.0, w - 2.0 * focus_pad);
        }
        if (h > 0.0 && h < track_h + 2.0 * focus_pad) {
            track_h = std::max(8.0, h - 2.0 * focus_pad);
        }

        std::string anchor = resolve_token_str("--anchor", vars, "w");
        double track_x = resolve_token("--switch-pad-x", vars, 4.0);
        double text_spacing = resolve_token("--switch-text-spacing", vars, 10.0);
        double est_text_w = resolve_token("--text-w", vars, static_cast<double>(sw_text.length()) * 7.5);
        double total_sw_w = track_w + (sw_text.empty() ? 0.0 : text_spacing + est_text_w);
        if (anchor == "center" && w > total_sw_w) {
            track_x = (w - total_sw_w) / 2.0;
        } else if ((anchor == "e" || anchor == "right") && w > total_sw_w) {
            track_x = w - total_sw_w - resolve_token("--switch-pad-x", vars, 4.0);
        } else if (sw_text.empty() && w > track_w) {
            track_x = (w - track_w) / 2.0;
        }
        track_x = std::max(focus_pad, track_x);

        double track_y = (h > track_h) ? (h - track_h) / 2.0 : focus_pad;
        track_y = std::max(focus_pad, track_y);

        double r = track_h / 2.0;
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;
        std::string track_bg = is_checked ? "--active-bg" : "--track-bg";
        Color track_col = is_checked ? Color(208, 188, 255) : Color(54, 52, 59);

        b.fill_rounded_rect_var(track_x, track_y, track_w, track_h, r, r, track_bg, "", "", track_col);

        double thumb_inset = resolve_token("--switch-thumb-inset", vars, 4.0);
        double thumb_r = std::max(2.0, r - thumb_inset);
        double thumb_cy = track_y + track_h / 2.0;
        double thumb_margin = thumb_r + thumb_inset;
        double thumb_cx = is_checked ? (track_x + track_w - thumb_margin) : (track_x + thumb_margin);

        double thumb_shadow_blur = resolve_token("--switch-thumb-shadow-blur", vars, 2.0);
        double thumb_shadow_y = resolve_token("--switch-thumb-shadow-y", vars, 1.0);

        // Thumb drop shadow
        b.draw_shadow_rounded_rect_var(
            thumb_cx - thumb_r, thumb_cy - thumb_r + 0.5,
            thumb_r * 2.0, thumb_r * 2.0, thumb_r, thumb_r,
            thumb_shadow_blur, 0.0, 0.0, thumb_shadow_y,
            "--btn-shadow", "", "", "",
            Color(0, 0, 0, 50)
        );

        std::string thumb_var = is_checked ? "--thumb-active-bg" : "--thumb-bg";
        Color thumb_col = is_checked ? Color(56, 30, 114) : Color(208, 188, 255);
        b.fill_circle_var(thumb_cx, thumb_cy, thumb_r, thumb_var, "", thumb_col);

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            double focus_ring_w = resolve_token("--focus-ring-width", vars, 2.0);
            double focus_ring_pad = resolve_token("--focus-ring-pad", vars, 1.5);
            b.stroke_rounded_rect_var(
                track_x - focus_ring_pad, track_y - focus_ring_pad,
                track_w + 2.0 * focus_ring_pad, track_h + 2.0 * focus_ring_pad,
                r + focus_ring_pad, r + focus_ring_pad,
                "--focus-ring-color", focus_ring_w, "", "", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }

        if (!sw_text.empty()) {
            double text_spacing = resolve_token("--switch-text-spacing", vars, 10.0);
            float font_size = static_cast<float>(resolve_token("--switch-font-size", vars, 13.0));
            std::string font_family = resolve_token_str("--switch-font-family", vars, "sans-serif");
            double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);
            b.draw_text_var(
                sw_text, track_x + track_w + text_spacing, h / 2.0 + font_size * baseline_offset,
                font_size, font_family,
                "--fg", "--text", "--font-size",
                Color(230, 224, 233), 0 /* left */
            );
        }
        return b;
    }

    if (key_cls == "checkbox") {
        std::string cb_text = resolve_token_str("--text", vars, "");
        double focus_pad = resolve_token("--checkbox-focus-pad", vars, 3.5);
        double box_size = resolve_token("--checkbox-size", vars, 18.0);
        if (w > 0.0 && w < box_size + 2.0 * focus_pad) {
            box_size = std::max(8.0, w - 2.0 * focus_pad);
        }
        if (h > 0.0 && h < box_size + 2.0 * focus_pad) {
            box_size = std::max(8.0, std::min(box_size, h - 2.0 * focus_pad));
        }

        std::string anchor = resolve_token_str("--anchor", vars, "w");
        double box_x = resolve_token("--checkbox-pad-x", vars, 4.0);
        double text_spacing = resolve_token("--checkbox-text-spacing", vars, 8.0);
        double est_text_w = resolve_token("--text-w", vars, static_cast<double>(cb_text.length()) * 7.5);
        double total_cb_w = box_size + (cb_text.empty() ? 0.0 : text_spacing + est_text_w);
        if (anchor == "center" && w > total_cb_w) {
            box_x = (w - total_cb_w) / 2.0;
        } else if ((anchor == "e" || anchor == "right") && w > total_cb_w) {
            box_x = w - total_cb_w - resolve_token("--checkbox-pad-x", vars, 4.0);
        } else if (cb_text.empty() && w > box_size) {
            box_x = (w - box_size) / 2.0;
        }
        box_x = std::max(focus_pad, box_x);

        double box_y = (h > box_size) ? (h - box_size) / 2.0 : focus_pad;
        box_y = std::max(focus_pad, box_y);
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;

        double box_radius = resolve_token("--checkbox-radius", vars, 4.0);
        double box_border_w = resolve_token("--checkbox-border-w", vars, 1.5);
        double stroke_w = resolve_token("--checkbox-stroke-w", vars, 2.0);

        if (!is_checked) {
            b.fill_rounded_rect_var(box_x, box_y, box_size, box_size, box_radius, box_radius, "--box-bg", "", "", Color(37, 35, 42));
            b.stroke_rounded_rect_var(box_x, box_y, box_size, box_size, box_radius, box_radius, "--box-border", box_border_w, "", "", "--border-w", Color(73, 69, 79));
        } else {
            b.fill_rounded_rect_var(box_x, box_y, box_size, box_size, box_radius, box_radius, "--active-bg", "", "", Color(208, 188, 255));
            b.stroke_rounded_rect_var(box_x, box_y, box_size, box_size, box_radius, box_radius, "--active-bg", box_border_w, "", "", "--border-w", Color(208, 188, 255));
            b.draw_line_var(box_x + 4.0, box_y + 9.0, box_x + 8.0, box_y + 13.0, "--check-color", stroke_w, "", Color(56, 30, 114));
            b.draw_line_var(box_x + 8.0, box_y + 13.0, box_x + 14.0, box_y + 5.0, "--check-color", stroke_w, "", Color(56, 30, 114));
        }

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            double focus_ring_w = resolve_token("--focus-ring-width", vars, 2.0);
            double focus_ring_pad = resolve_token("--focus-ring-pad", vars, 1.5);
            b.stroke_rounded_rect_var(
                box_x - focus_ring_pad, box_y - focus_ring_pad,
                box_size + 2.0 * focus_ring_pad, box_size + 2.0 * focus_ring_pad,
                box_radius + focus_ring_pad, box_radius + focus_ring_pad,
                "--focus-ring-color", focus_ring_w, "", "", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }

        if (!cb_text.empty()) {
            double text_spacing = resolve_token("--checkbox-text-spacing", vars, 8.0);
            float font_size = static_cast<float>(resolve_token("--checkbox-font-size", vars, 13.0));
            std::string font_family = resolve_token_str("--checkbox-font-family", vars, "sans-serif");
            double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);
            b.draw_text_var(
                cb_text, box_x + box_size + text_spacing, h / 2.0 + font_size * baseline_offset,
                font_size, font_family,
                "--fg", "--text", "--font-size",
                Color(230, 224, 233), 0 /* left */
            );
        }
        return b;
    }

    if (key_cls == "radio") {
        std::string radio_text = resolve_token_str("--text", vars, "");
        double focus_pad = resolve_token("--radio-focus-pad", vars, 3.5);
        double cr = resolve_token("--radio-radius", vars, 8.0);
        if (w > 0.0 && w < 2.0 * (cr + focus_pad)) {
            cr = std::max(4.0, (w - 2.0 * focus_pad) / 2.0);
        }
        if (h > 0.0 && h < 2.0 * (cr + focus_pad)) {
            cr = std::max(4.0, std::min(cr, (h - 2.0 * focus_pad) / 2.0));
        }

        std::string anchor = resolve_token_str("--anchor", vars, "w");
        double pad_x = resolve_token("--radio-pad-x", vars, 4.0);
        double text_spacing = resolve_token("--radio-text-spacing", vars, 8.0);
        double est_text_w = resolve_token("--text-w", vars, static_cast<double>(radio_text.length()) * 7.5);
        double total_rd_w = 2.0 * cr + (radio_text.empty() ? 0.0 : text_spacing + est_text_w);
        double cx = cr + pad_x;
        if (anchor == "center" && w > total_rd_w) {
            cx = (w - total_rd_w) / 2.0 + cr;
        } else if ((anchor == "e" || anchor == "right") && w > total_rd_w) {
            cx = w - total_rd_w - pad_x + cr;
        } else if (radio_text.empty() && w > 2.0 * cr) {
            cx = w / 2.0;
        }
        cx = std::max(cr + focus_pad, cx);
        double cy = h / 2.0;
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;

        double border_w = resolve_token("--radio-border-w", vars, 1.5);
        double dot_r = resolve_token("--radio-dot-r", vars, 4.0);

        if (!is_checked) {
            b.fill_circle_var(cx, cy, cr, "--radio-bg", "", Color(37, 35, 42));
            b.stroke_circle_var(cx, cy, cr, "--radio-border", border_w, "", "", Color(73, 69, 79));
        } else {
            b.fill_circle_var(cx, cy, cr, "--radio-bg", "", Color(37, 35, 42));
            b.stroke_circle_var(cx, cy, cr, "--active-bg", border_w, "", "", Color(208, 188, 255));
            b.fill_circle_var(cx, cy, dot_r, "--dot-color", "", Color(208, 188, 255));
        }

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            double focus_ring_w = resolve_token("--focus-ring-width", vars, 2.0);
            double focus_ring_pad = resolve_token("--focus-ring-pad", vars, 2.5);
            b.stroke_circle_var(cx, cy, cr + focus_ring_pad, "--focus-ring-color", focus_ring_w, "", "--focus-ring-width", Color(208, 188, 255));
        }

        if (!radio_text.empty()) {
            double text_spacing = resolve_token("--radio-text-spacing", vars, 8.0);
            float font_size = static_cast<float>(resolve_token("--radio-font-size", vars, 13.0));
            std::string font_family = resolve_token_str("--radio-font-family", vars, "sans-serif");
            double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);
            b.draw_text_var(
                radio_text, cx + cr + text_spacing, h / 2.0 + font_size * baseline_offset,
                font_size, font_family,
                "--fg", "--text", "--font-size",
                Color(230, 224, 233), 0 /* left */
            );
        }
        return b;
    }

    if (key_cls == "slider") {
        double pad = resolve_token("--slider-pad-x", vars, 12.0);
        double track_w = std::max(10.0, w - pad * 2.0);
        double track_h = resolve_token("--slider-track-h", vars, 4.0);
        double track_radius = resolve_token("--slider-track-radius", vars, 2.0);
        double track_y = (h > track_h) ? (h - track_h) / 2.0 : 0.0;
        double thumb_pos = 0.0;
        auto it = vars.find("thumb-pos"_hash);
        if (it != vars.end()) {
            try { thumb_pos = std::clamp(std::stod(it->second), 0.0, 1.0); } catch (...) {}
        }

        b.fill_rounded_rect_var(pad, track_y, track_w, track_h, track_radius, track_radius, "--track-bg", "", "", Color(54, 52, 59));

        double active_w = track_w * thumb_pos;
        if (active_w > 0.0) {
            b.fill_rounded_rect_var(pad, track_y, active_w, track_h, track_radius, track_radius, "--active-track-bg", "", "", Color(208, 188, 255));
        }

        double thumb_cx = pad + active_w;
        double thumb_cy = h / 2.0;
        double thumb_r = resolve_token("--slider-thumb-r", vars, 7.0);
        double thumb_border_w = resolve_token("--slider-thumb-border-w", vars, 1.5);
        double thumb_shadow_blur = resolve_token("--slider-thumb-shadow-blur", vars, 2.0);
        double thumb_shadow_y = resolve_token("--slider-thumb-shadow-y", vars, 1.0);

        // Thumb drop shadow
        b.draw_shadow_rounded_rect_var(
            thumb_cx - thumb_r, thumb_cy - thumb_r + 0.5,
            thumb_r * 2.0, thumb_r * 2.0, thumb_r, thumb_r,
            thumb_shadow_blur, 0.0, 0.0, thumb_shadow_y,
            "--btn-shadow", "", "", "",
            Color(0, 0, 0, 50)
        );

        b.fill_circle_var(thumb_cx, thumb_cy, thumb_r, "--thumb-bg", "--thumb-r", Color(208, 188, 255));
        b.stroke_circle_var(thumb_cx, thumb_cy, thumb_r, "--thumb-border", thumb_border_w, "--thumb-r", "", Color(255, 255, 255));

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            double focus_ring_w = resolve_token("--focus-ring-width", vars, 2.0);
            double focus_ring_pad = resolve_token("--focus-ring-pad", vars, 2.5);
            b.stroke_circle_var(thumb_cx, thumb_cy, thumb_r + focus_ring_pad, "--focus-ring-color", focus_ring_w, "", "--focus-ring-width", Color(208, 188, 255));
        }
        return b;
    }

    if (key_cls == "progressbar") {
        double bar_h = resolve_token("--progress-h", vars, std::min(h, 6.0));
        double bar_radius = resolve_token("--progress-radius", vars, 3.0);
        double bar_y = (h > bar_h) ? (h - bar_h) / 2.0 : 0.0;
        double progress = 0.0;
        auto it = vars.find("progress"_hash);
        if (it != vars.end()) {
            try { progress = std::clamp(std::stod(it->second), 0.0, 1.0); } catch (...) {}
        }

        b.fill_rounded_rect_var(0.0, bar_y, w, bar_h, bar_radius, bar_radius, "--track-bg", "--rx", "--ry", Color(54, 52, 59));
        double prog_w = w * progress;
        if (prog_w > 0.0) {
            b.fill_rounded_rect_var(0.0, bar_y, prog_w, bar_h, bar_radius, bar_radius, "--bar-bg", "--rx", "--ry", Color(208, 188, 255));
        }
        return b;
    }

    if (key_cls == "badge") {
        double rx = resolve_token("--badge-radius", vars, std::min(w, h) / 2.0);
        b.fill_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--badge-bg", "--rx", "--ry", Color(74, 68, 88));
        std::string badge_text = resolve_token_str("--text", vars, "");
        float font_size = static_cast<float>(resolve_token("--badge-font-size", vars, 11.0));
        std::string font_family = resolve_token_str("--badge-font-family", vars, "sans-serif");
        int font_weight = static_cast<int>(resolve_token("--badge-font-weight", vars, 600.0));
        double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);
        b.draw_text_var(
            badge_text, w / 2.0, h / 2.0 + font_size * baseline_offset, font_size, font_family,
            "--badge-fg", "--text", "--font-size",
            Color(230, 224, 233), 1 /* center */, font_weight
        );
        return b;
    }

    if (key_cls == "card") {
        double pad_x = resolve_token("--card-pad-x", vars, 10.0);
        double pad_top = resolve_token("--card-pad-top", vars, 8.0);
        double pad_bottom = resolve_token("--card-pad-bottom", vars, 12.0);
        double cx = pad_x;
        double cy = pad_top;
        double cw = std::max(10.0, w - 2.0 * pad_x);
        double ch = std::max(10.0, h - pad_top - pad_bottom);
        double card_radius = resolve_token("--card-radius", vars, 12.0);
        double border_w = resolve_token("--card-border-w", vars, 1.0);
        double shadow_blur = resolve_token("--card-shadow-blur", vars, 8.0);
        double shadow_y = resolve_token("--card-shadow-y", vars, 3.0);

        b.draw_card_var(
            cx, cy, cw, ch,
            card_radius, card_radius,
            "--card-bg", "--card-border",
            border_w, shadow_blur, 0.0, 0.0, shadow_y,
            "--card-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 40)
        );
        return b;
    }

    if (key_cls == "frame") {
        double rx = resolve_token("--frame-radius", vars, 12.0);
        auto it_rx = vars.find("rx"_hash);
        if (it_rx != vars.end()) {
            try { rx = std::stod(it_rx->second); } catch (...) {}
        }
        double bw = resolve_token("--frame-border-w", vars, 0.0);
        auto it_bw = vars.find("bw"_hash);
        if (it_bw != vars.end()) {
            try { bw = std::stod(it_bw->second); } catch (...) {}
        }
        b.fill_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--bg", "--rx", "--ry", Color(29, 27, 32));
        if (bw > 0.0) {
            b.stroke_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--border", bw, "--rx", "--ry", "--bw", Color(73, 69, 79));
        }
        return b;
    }

    if (key_cls == "circular_progress" || key_cls == "gauge") {
        double cx = w / 2.0;
        double cy = h / 2.0;
        double sw = resolve_token("--circular-stroke-w", vars, 8.0);
        auto it_sw = vars.find("stroke-width"_hash);
        if (it_sw != vars.end()) {
            try { sw = std::stod(it_sw->second); } catch (...) {}
        }
        double r = std::max(2.0, std::min(cx, cy) - sw / 2.0 - 2.0);

        double start_angle = -1.5707963267948966; // -90 deg
        double sweep_angle = 6.283185307179586;   // 360 deg
        auto it_sa = vars.find("start-angle"_hash);
        if (it_sa != vars.end()) {
            try { start_angle = std::stod(it_sa->second) * 3.141592653589793 / 180.0; } catch (...) {}
        }
        auto it_swp = vars.find("sweep-angle"_hash);
        if (it_swp != vars.end()) {
            try { sweep_angle = std::stod(it_swp->second) * 3.141592653589793 / 180.0; } catch (...) {}
        }

        double progress = 0.0;
        auto it_p = vars.find("progress"_hash);
        if (it_p != vars.end()) {
            try { progress = std::clamp(std::stod(it_p->second), 0.0, 1.0); } catch (...) {}
        }

        if (std::abs(sweep_angle) >= 6.28) {
            b.stroke_circle_var(cx, cy, r, "--track-bg", sw, "", "--stroke-width", Color(39, 39, 42));
        } else {
            b.stroke_arc_var(cx, cy, r, start_angle, sweep_angle, "--track-bg", sw, "--stroke-width", Color(39, 39, 42));
        }

        if (progress > 0.001) {
            double arc_swp = sweep_angle * progress;
            b.stroke_arc_var(cx, cy, r, start_angle, arc_swp, "--primary", sw, "--stroke-width", Color(139, 92, 246));
        }

        std::string show_val = "1";
        auto it_sv = vars.find("show-value"_hash);
        if (it_sv != vars.end()) show_val = it_sv->second;
        if (show_val != "0" && show_val != "false") {
            float font_sz = static_cast<float>(std::max(10.0, r * 0.42));
            std::string font_family = resolve_token_str("--circular-font-family", vars, "sans-serif");
            std::string title = "";
            auto it_t = vars.find("title"_hash);
            if (it_t != vars.end()) title = it_t->second;

            if (!title.empty()) {
                b.draw_text_var("", cx, cy - font_sz * 0.1, font_sz, font_family, "--fg", "--text", "", Color(230, 224, 233), 1 /* center */, 700);
                b.draw_text_var(title, cx, cy + font_sz * 0.55, font_sz * 0.45f, font_family, "--text-muted", "--title", "", Color(161, 161, 170), 1 /* center */, 400);
            } else {
                b.draw_text_var("", cx, cy + font_sz * 0.35, font_sz, font_family, "--fg", "--text", "", Color(230, 224, 233), 1 /* center */, 700);
            }
        }
        return b;
    }

    if (key_cls == "segmented_button") {
        int count = 2;
        auto it_c = vars.find("count"_hash);
        if (it_c != vars.end()) {
            try { count = std::max(1, std::stoi(it_c->second)); } catch (...) {}
        }
        int selected = 0;
        auto it_s = vars.find("selected-index"_hash);
        if (it_s != vars.end()) {
            try { selected = std::clamp(std::stoi(it_s->second), 0, count - 1); } catch (...) {}
        }

        double pill_pad = resolve_token("--segmented-pill-padding", vars, 3.0);
        double border_w = resolve_token("--segmented-border-w", vars, 1.0);
        double rx = h / 2.0;

        // Background capsule container
        b.fill_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--card-bg", "", "", Color(37, 35, 42));
        b.stroke_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--card-border", border_w, "", "", "", Color(73, 69, 79));

        double seg_w = w / static_cast<double>(count);

        // Active segment indicator pill
        double act_x = selected * seg_w + pill_pad;
        double act_w = std::max(10.0, seg_w - 2.0 * pill_pad);
        double act_h = h - 2.0 * pill_pad;
        double act_rx = act_h / 2.0;
        b.fill_rounded_rect_var(act_x, pill_pad, act_w, act_h, act_rx, act_rx, "--primary", "", "", Color(139, 92, 246));

        // Dividers between segments (skip borders adjacent to active segment)
        for (int i = 1; i < count; ++i) {
            if (i != selected && i != selected + 1) {
                double div_x = i * seg_w;
                b.draw_line_var(div_x, 2.0 * pill_pad, div_x, h - 2.0 * pill_pad, "--card-border", border_w, "", Color(73, 69, 79));
            }
        }

        // Segment labels
        float font_size = static_cast<float>(resolve_token("--segmented-font-size", vars, 13.0));
        std::string font_family = resolve_token_str("--segmented-font-family", vars, "sans-serif");
        double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);

        for (int i = 0; i < count; ++i) {
            std::string var_name = "--seg-" + std::to_string(i) + "-text";
            std::string txt = "";
            auto it_txt = vars.find(fnv1a64(extract_var_view(var_name)));
            if (it_txt != vars.end()) txt = it_txt->second;
            double seg_cx = (i + 0.5) * seg_w;
            double txt_y = h / 2.0 + font_size * baseline_offset;
            std::string col_var = (i == selected) ? "--primary-fg" : "--fg";
            Color fallback_col = (i == selected) ? Color(255, 255, 255) : Color(230, 224, 233);
            b.draw_text_var(txt, seg_cx, txt_y, font_size, font_family, col_var, var_name, "", fallback_col, 1 /* center */, (i == selected) ? 600 : 500);
        }
        return b;
    }

    if (key_cls == "range_slider") {
        double pad_x = resolve_token("--range-slider-pad-x", vars, 14.0);
        double th = resolve_token("--range-slider-track-h", vars, 8.0);
        double ty = (h - th) / 2.0;
        double track_w = std::max(10.0, w - 2.0 * pad_x);

        double min_p = 0.25, max_p = 0.75;
        auto it_min = vars.find("thumb-min-pos"_hash);
        if (it_min != vars.end()) { try { min_p = std::clamp(std::stod(it_min->second), 0.0, 1.0); } catch (...) {} }
        auto it_max = vars.find("thumb-max-pos"_hash);
        if (it_max != vars.end()) { try { max_p = std::clamp(std::stod(it_max->second), 0.0, 1.0); } catch (...) {} }
        if (min_p > max_p) std::swap(min_p, max_p);

        // Inactive background track
        b.fill_rounded_rect_var(pad_x, ty, track_w, th, th / 2.0, th / 2.0, "--track-bg", "", "", Color(39, 39, 42));

        // Active range highlight track
        double act_x = pad_x + min_p * track_w;
        double act_w = std::max(4.0, (max_p - min_p) * track_w);
        b.fill_rounded_rect_var(act_x, ty, act_w, th, th / 2.0, th / 2.0, "--primary", "", "", Color(139, 92, 246));

        double thumb_r = resolve_token("--range-slider-thumb-r", vars, 10.0);
        double thumb_border_w = resolve_token("--range-slider-thumb-border-w", vars, 2.0);

        // Left thumb circle
        double t1_cx = pad_x + min_p * track_w;
        b.fill_circle_var(t1_cx, h / 2.0, thumb_r, "--thumb-color", "", Color(139, 92, 246));
        b.stroke_circle_var(t1_cx, h / 2.0, thumb_r, "--thumb-border", thumb_border_w, "", "", Color(255, 255, 255));

        // Right thumb circle
        double t2_cx = pad_x + max_p * track_w;
        b.fill_circle_var(t2_cx, h / 2.0, thumb_r, "--thumb-color", "", Color(139, 92, 246));
        b.stroke_circle_var(t2_cx, h / 2.0, thumb_r, "--thumb-border", thumb_border_w, "", "", Color(255, 255, 255));
        return b;
    }

    if (key_cls == "sparkline") {
        std::string raw_data = "";
        auto it_d = vars.find("data"_hash);
        if (it_d != vars.end()) raw_data = it_d->second;

        std::vector<double> pts;
        std::size_t start = 0;
        while (start < raw_data.size()) {
            auto pos = raw_data.find(',', start);
            std::string tok = (pos == std::string::npos) ? raw_data.substr(start) : raw_data.substr(start, pos - start);
            try { if (!tok.empty()) pts.push_back(std::stod(tok)); } catch (...) {}
            if (pos == std::string::npos) break;
            start = pos + 1;
        }

        double pad = resolve_token("--sparkline-pad", vars, 6.0);
        double pw = std::max(10.0, w - 2.0 * pad);
        double ph = std::max(10.0, h - 2.0 * pad);

        if (pts.size() >= 2) {
            double min_v = *std::min_element(pts.begin(), pts.end());
            double max_v = *std::max_element(pts.begin(), pts.end());
            double span = std::max(0.001, max_v - min_v);

            double step_x = pw / static_cast<double>(pts.size() - 1);
            double prev_x = pad;
            double prev_y = pad + ph - ((pts[0] - min_v) / span) * ph;
            double line_w = resolve_token("--sparkline-line-w", vars, 2.0);
            double dot_r = resolve_token("--sparkline-dot-r", vars, 4.0);

            for (std::size_t i = 1; i < pts.size(); ++i) {
                double cur_x = pad + i * step_x;
                double cur_y = pad + ph - ((pts[i] - min_v) / span) * ph;
                b.draw_line_var(prev_x, prev_y, cur_x, cur_y, "--primary", line_w, "", Color(139, 92, 246));
                prev_x = cur_x;
                prev_y = cur_y;
            }

            // Endpoint glowing dot
            b.fill_circle_var(prev_x, prev_y, dot_r, "--primary", "", Color(139, 92, 246));
            b.fill_circle_var(prev_x, prev_y, dot_r / 2.0, "--card-bg", "", Color(37, 35, 42));
        }
        return b;
    }

    if (key_cls == "combobox") {
        b.clear_var("--parent-bg");

        double pad_x = resolve_token("--input-pad-x", vars, 3.0);
        double pad_top = resolve_token("--input-pad-top", vars, 2.0);
        double pad_bottom = resolve_token("--input-pad-bottom", vars, 4.0);
        double input_radius = resolve_token("--input-radius", vars, 8.0);
        double bx = pad_x;
        double by = pad_top;
        double bw = std::max(4.0, w - 2.0 * pad_x);
        double bh = std::max(4.0, h - pad_top - pad_bottom);

        std::string border_col = ((state & ControllerPseudoState::StateFocused) != 0) ? "--input-focus"
                               : ((state & ControllerPseudoState::StateHover) != 0)   ? "--card-border"
                               : "--input-border";
        double border_w = ((state & ControllerPseudoState::StateFocused) != 0)
            ? resolve_token("--input-border-width-focus", vars, 1.5)
            : resolve_token("--input-border-width", vars, 1.0);
        Color fallback_border = ((state & ControllerPseudoState::StateFocused) != 0) ? Color(208, 188, 255) : Color(73, 69, 79);

        double shadow_blur = resolve_token("--input-shadow-blur", vars, 2.0);
        double shadow_off_y = resolve_token("--input-shadow-y", vars, 0.8);
        Color fallback_shadow(0, 0, 0, 24);

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            shadow_blur = resolve_token("--input-shadow-blur-focus", vars, 3.2);
            shadow_off_y = resolve_token("--input-shadow-y-focus", vars, 1.0);
            fallback_shadow = Color(0, 0, 0, 36);
        } else if ((state & ControllerPseudoState::StateHover) != 0) {
            shadow_blur = resolve_token("--input-shadow-blur-hover", vars, 2.6);
            shadow_off_y = resolve_token("--input-shadow-y-focus", vars, 1.0);
            fallback_shadow = Color(0, 0, 0, 30);
        }

        b.draw_card_var(
            bx, by, bw, bh,
            input_radius, input_radius,
            "--input-bg", border_col,
            border_w, shadow_blur, 0.0, 0.0, shadow_off_y,
            "--input-shadow",
            "--rx", "--ry", "--bw",
            Color(29, 27, 32), fallback_border, fallback_shadow
        );

        // Value text
        double txt_pad_x = resolve_token("--combobox-text-pad-x", vars, 12.0);
        double txt_x = bx + txt_pad_x;
        float font_size = static_cast<float>(resolve_token("--input-font-size", vars, 13.0));
        std::string font_family = resolve_token_str("--input-font-family", vars, "sans-serif");
        double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);
        double txt_y = by + bh / 2.0 + font_size * baseline_offset;
        std::string combo_text = resolve_token_str("--text", vars, "");
        b.draw_text_var(combo_text, txt_x, txt_y, font_size, font_family, "--fg", "--text", "", Color(230, 224, 233), 0 /* left */, 500);

        // Chevron arrow indicator at right
        double arr_cx = bx + bw - 14.0;
        double arr_cy = by + bh / 2.0;
        double arrow_sz = resolve_token("--combobox-arrow-size", vars, 4.5);
        b.draw_line(arr_cx - arrow_sz, arr_cy - arrow_sz * 0.55, arr_cx, arr_cy + arrow_sz * 0.55, Color(161, 161, 170), 1.6);
        b.draw_line(arr_cx, arr_cy + arrow_sz * 0.55, arr_cx + arrow_sz, arr_cy - arrow_sz * 0.55, Color(161, 161, 170), 1.6);
        return b;
    }

    if (key_cls == "scrollbar") {
        b.clear_var("--parent-bg");
        // Thumb / scrollbar auto-hide when content completely fits without scrolling
        auto it_hid = vars.find("thumb-hidden"_hash);
        if (it_hid != vars.end() && it_hid->second == "1") {
            return b;
        }

        bool is_horiz = false;
        auto it_ori = vars.find("orientation"_hash);
        if (it_ori != vars.end() && it_ori->second == "horizontal") {
            is_horiz = true;
        } else if (w > h * 1.5) {
            is_horiz = true;
        }

        // Draw track
        double track_r = is_horiz ? (h / 2.0) : (w / 2.0);
        b.fill_rounded_rect_var(0.0, 0.0, w, h, track_r, track_r, "--track-bg", "", "", Color(39, 39, 42));

        double thumb_pos = 0.0;
        double thumb_sz = 0.3;
        auto it_pos = vars.find("thumb-pos"_hash);
        if (it_pos != vars.end()) { try { thumb_pos = std::clamp(std::stod(it_pos->second), 0.0, 1.0); } catch (...) {} }
        auto it_sz = vars.find("thumb-size"_hash);
        if (it_sz != vars.end()) { try { thumb_sz = std::clamp(std::stod(it_sz->second), 0.05, 1.0); } catch (...) {} }

        if (thumb_sz >= 0.999) {
            return b; // Content fits without scrolling
        }

        double sb_pad = resolve_token("--scrollbar-pad", vars, 1.5);
        double min_sz_token = resolve_token("--scrollbar-thumb-min-size", vars, 28.0);

        if (is_horiz) {
            double min_sz = std::min(w, min_sz_token);
            double max_sz = std::max(min_sz, w * 0.30);
            double thumb_w = std::clamp(w * thumb_sz, min_sz, max_sz);
            double available_w = std::max(0.0, w - thumb_w);
            double thumb_x = std::clamp(thumb_pos * available_w, 0.0, available_w);
            b.fill_rounded_rect_var(thumb_x, sb_pad, thumb_w, h - 2.0 * sb_pad, (h - 2.0 * sb_pad) / 2.0, (h - 2.0 * sb_pad) / 2.0, "--thumb-color", "", "", Color(139, 92, 246));
        } else {
            double min_sz = std::min(h, min_sz_token);
            double max_sz = std::max(min_sz, h * 0.30);
            double thumb_h = std::clamp(h * thumb_sz, min_sz, max_sz);
            double available_h = std::max(0.0, h - thumb_h);
            double thumb_y = std::clamp(thumb_pos * available_h, 0.0, available_h);
            b.fill_rounded_rect_var(sb_pad, thumb_y, w - 2.0 * sb_pad, thumb_h, (w - 2.0 * sb_pad) / 2.0, (w - 2.0 * sb_pad) / 2.0, "--thumb-color", "", "", Color(139, 92, 246));
        }
        return b;
    }

    if (key_cls == "table") {
        double header_h = resolve_token("--table-header-h", vars, 38.0);
        auto it_hh = vars.find("header-height"_hash);
        if (it_hh != vars.end()) { try { header_h = std::stod(it_hh->second); } catch (...) {} }

        double table_radius = resolve_token("--table-radius", vars, 8.0);
        double table_border_w = resolve_token("--table-border-w", vars, 1.0);

        // Background
        b.fill_rounded_rect_var(0.0, 0.0, w, h, table_radius, table_radius, "--card-bg", "", "", Color(37, 35, 42));
        b.stroke_rounded_rect_var(0.0, 0.0, w, h, table_radius, table_radius, "--card-border", table_border_w, "", "", "", Color(73, 69, 79));

        // Header bottom divider line
        b.draw_line_var(0.0, header_h, w, header_h, "--card-border", table_border_w, "", Color(73, 69, 79));
        return b;
    }

    if (key_cls == "label") {
        std::string lbl_text = resolve_token_str("--text", vars, "");
        double pad_x = resolve_token("--label-pad-x", vars, 2.0);
        float font_size = static_cast<float>(resolve_token("--label-font-size", vars, 13.0));
        std::string font_family = resolve_token_str("--label-font-family", vars, "sans-serif");
        int font_weight = static_cast<int>(resolve_token("--label-font-weight", vars, 400.0));
        double baseline_offset = resolve_token("--text-baseline-offset", vars, 0.35);

        std::string anchor = resolve_token_str("--anchor", vars, "w");
        double text_x = pad_x;
        int align_mode = 0; // left
        if (anchor == "center" || anchor == "c") {
            text_x = w / 2.0;
            align_mode = 1; // center
        } else if (anchor == "e" || anchor == "right") {
            text_x = w - pad_x;
            align_mode = 2; // right
        }

        b.draw_text_var(
            lbl_text, text_x, h / 2.0 + font_size * baseline_offset, font_size, font_family,
            "--fg", "--text", "--font-size",
            Color(230, 224, 233), align_mode, font_weight
        );
        return b;
    }

    if (key_cls == "entry" || key_cls == "textbox_frame" || key_cls == "search_entry") {
        b.clear_var("--parent-bg");

        double pad_x = resolve_token("--input-pad-x", vars, 3.0);
        double pad_top = resolve_token("--input-pad-top", vars, 2.0);
        double pad_bottom = resolve_token("--input-pad-bottom", vars, 4.0);
        double input_radius = resolve_token("--input-radius", vars, 8.0);
        double bx = pad_x;
        double by = pad_top;
        double bw = std::max(4.0, w - 2.0 * pad_x);
        double bh = std::max(4.0, h - pad_top - pad_bottom);

        std::string border_col = ((state & ControllerPseudoState::StateFocused) != 0) ? "--input-focus"
                               : ((state & ControllerPseudoState::StateHover) != 0)   ? "--card-border"
                               : "--input-border";
        double border_w = ((state & ControllerPseudoState::StateFocused) != 0)
            ? resolve_token("--input-border-width-focus", vars, 1.5)
            : resolve_token("--input-border-width", vars, 1.0);
        Color fallback_border = ((state & ControllerPseudoState::StateFocused) != 0) ? Color(208, 188, 255) : Color(73, 69, 79);

        double shadow_blur = resolve_token("--input-shadow-blur", vars, 2.0);
        double shadow_off_y = resolve_token("--input-shadow-y", vars, 0.8);
        Color fallback_shadow(0, 0, 0, 24);

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            shadow_blur = resolve_token("--input-shadow-blur-focus", vars, 3.2);
            shadow_off_y = resolve_token("--input-shadow-y-focus", vars, 1.0);
            fallback_shadow = Color(0, 0, 0, 36);
        } else if ((state & ControllerPseudoState::StateHover) != 0) {
            shadow_blur = resolve_token("--input-shadow-blur-hover", vars, 2.6);
            shadow_off_y = resolve_token("--input-shadow-y-focus", vars, 1.0);
            fallback_shadow = Color(0, 0, 0, 30);
        }

        b.draw_card_var(
            bx, by, bw, bh,
            input_radius, input_radius,
            "--input-bg", border_col,
            border_w, shadow_blur, 0.0, 0.0, shadow_off_y,
            "--input-shadow",
            "--rx", "--ry", "--bw",
            Color(29, 27, 32), fallback_border, fallback_shadow
        );

        if (key_cls == "search_entry") {
            double icon_pad_x = resolve_token("--search-icon-pad-x", vars, 14.0);
            double icon_cx = bx + icon_pad_x;
            double icon_cy = by + bh / 2.0;
            double icon_sz = resolve_token("--search-icon-size", vars, 4.5);
            double line_w = resolve_token("--search-icon-line-w", vars, 1.5);
            double handle_w = resolve_token("--search-icon-handle-w", vars, 1.8);

            b.stroke_circle_var(icon_cx - 2.0, icon_cy - 2.0, icon_sz, "--text-muted", line_w, "", "", Color(160, 160, 175));
            b.draw_line_var(icon_cx + 1.2, icon_cy + 1.2, icon_cx + 1.2 + icon_sz * 0.95, icon_cy + 1.2 + icon_sz * 0.95, "--text-muted", handle_w, "", Color(160, 160, 175));
        }
        return b;
    }

    return DrawBatch();
}

std::vector<std::string> DrawEngine::get_registered_classes() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    std::vector<std::string> res;
    for (const auto& [k, b] : batches_) {
        if (std::find(res.begin(), res.end(), k.widget_class) == res.end()) {
            res.push_back(k.widget_class);
        }
    }
    return res;
}

void DrawEngine::clear() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    batches_.clear();
}

void DrawEngine::reset_defaults() {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    batches_.clear();
    init_default_batches();
}

void DrawEngine::init_default_batches() {
    // -------------------------------------------------------------
    // 1. BUTTON
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        // Drop shadow + background card
        b.draw_card_var(
            0.0, 0.0, 0.0, 0.0,
            8.0, 8.0,
            "--btn-bg", "--btn-border",
            0.0, 2.0, 0.0, 0.0, 0.8,
            "--btn-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 28),
            "--w", "--h"
        );
        // Centered typography
        b.draw_text_var(
            "", 0.0, 0.0, 13.0f, "sans-serif",
            "--btn-fg", "--text", "--font-size",
            Color(255, 255, 255),
            1 /* center */, 500
        );
        // Focus ring
        b.stroke_rounded_rect_var(
            -2.0, -2.0, 0.0, 0.0,
            10.0, 10.0,
            "--focus-ring-color", 2.0,
            "--rx", "--ry", "--focus-ring-width",
            Color(0, 0, 0, 0),
            "--w_fr", "--h_fr"
        );
        register_batch("button", 0, b);
    }

    // -------------------------------------------------------------
    // 2. CHECKBOX
    // -------------------------------------------------------------
    {
        // Unchecked (normal)
        DrawBatch b_normal;
        b_normal.clear_var("--parent-bg");
        b_normal.fill_rounded_rect_var(4.0, 2.0, 18.0, 18.0, 4.0, 4.0, "--box-bg", "", "", Color(37, 35, 42), "--box-size", "--box-size");
        b_normal.stroke_rounded_rect_var(4.0, 2.0, 18.0, 18.0, 4.0, 4.0, "--box-border", 1.5, "", "", "--border-w", Color(73, 69, 79), "--box-size", "--box-size");
        b_normal.draw_text_var("", 30.0, 15.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_normal.stroke_rounded_rect_var(2.5, 0.5, 21.0, 21.0, 5.5, 5.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("checkbox", 0, b_normal);

        // Checked
        DrawBatch b_checked;
        b_checked.clear_var("--parent-bg");
        b_checked.fill_rounded_rect_var(4.0, 2.0, 18.0, 18.0, 4.0, 4.0, "--active-bg", "", "", Color(208, 188, 255), "--box-size", "--box-size");
        b_checked.stroke_rounded_rect_var(4.0, 2.0, 18.0, 18.0, 4.0, 4.0, "--active-bg", 1.5, "", "", "--border-w", Color(208, 188, 255), "--box-size", "--box-size");
        b_checked.draw_line_var(8.0, 11.0, 12.0, 15.0, "--check-color", 2.0, "", Color(56, 30, 114));
        b_checked.draw_line_var(12.0, 15.0, 18.0, 7.0, "--check-color", 2.0, "", Color(56, 30, 114));
        b_checked.draw_text_var("", 30.0, 15.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_checked.stroke_rounded_rect_var(2.5, 0.5, 21.0, 21.0, 5.5, 5.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("checkbox", ControllerPseudoState::StateChecked, b_checked);
    }

    // -------------------------------------------------------------
    // 3. RADIO
    // -------------------------------------------------------------
    {
        // Unselected
        DrawBatch b_normal;
        b_normal.clear_var("--parent-bg");
        b_normal.fill_circle_var(12.0, 11.0, 8.0, "--radio-bg", "", Color(37, 35, 42));
        b_normal.stroke_circle_var(12.0, 11.0, 8.0, "--radio-border", 1.5, "", "", Color(73, 69, 79));
        b_normal.draw_text_var("", 28.0, 15.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_normal.stroke_circle_var(12.0, 11.0, 10.5, "--focus-ring-color", 2.0, "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("radio", 0, b_normal);

        // Selected
        DrawBatch b_checked;
        b_checked.clear_var("--parent-bg");
        b_checked.fill_circle_var(12.0, 11.0, 8.0, "--radio-bg", "", Color(37, 35, 42));
        b_checked.stroke_circle_var(12.0, 11.0, 8.0, "--active-bg", 1.5, "", "", Color(208, 188, 255));
        b_checked.fill_circle_var(12.0, 11.0, 4.0, "--dot-color", "", Color(208, 188, 255));
        b_checked.draw_text_var("", 28.0, 15.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_checked.stroke_circle_var(12.0, 11.0, 10.5, "--focus-ring-color", 2.0, "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("radio", ControllerPseudoState::StateChecked, b_checked);
    }

    // -------------------------------------------------------------
    // 4. SWITCH
    // -------------------------------------------------------------
    {
        // Unchecked
        DrawBatch b_normal;
        b_normal.clear_var("--parent-bg");
        b_normal.fill_rounded_rect_var(4.0, 3.0, 40.0, 22.0, 11.0, 11.0, "--track-bg", "", "", Color(54, 52, 59));
        b_normal.fill_circle_var(15.0, 14.0, 7.0, "--thumb-bg", "", Color(208, 188, 255));
        b_normal.draw_text_var("", 54.0, 17.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_normal.stroke_rounded_rect_var(2.5, 1.5, 43.0, 25.0, 12.5, 12.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("switch", 0, b_normal);

        // Checked
        DrawBatch b_checked;
        b_checked.clear_var("--parent-bg");
        b_checked.fill_rounded_rect_var(4.0, 3.0, 40.0, 22.0, 11.0, 11.0, "--active-bg", "", "", Color(208, 188, 255));
        b_checked.fill_circle_var(33.0, 14.0, 7.0, "--thumb-active-bg", "", Color(56, 30, 114));
        b_checked.draw_text_var("", 54.0, 17.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_checked.stroke_rounded_rect_var(2.5, 1.5, 43.0, 25.0, 12.5, 12.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("switch", ControllerPseudoState::StateChecked, b_checked);
    }

    // -------------------------------------------------------------
    // 5. SLIDER
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        // Inactive track
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 4.0, 2.0, 2.0, "--track-bg", "", "", Color(54, 52, 59), "--w", "");
        // Active filled segment
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 4.0, 2.0, 2.0, "--active-track-bg", "", "", Color(208, 188, 255), "--active-w", "");
        // Thumb circle
        b.fill_circle_var(0.0, 0.0, 8.0, "--thumb-bg", "--thumb-r", Color(208, 188, 255));
        b.stroke_circle_var(0.0, 0.0, 8.0, "--thumb-border", 1.5, "--thumb-r", "", Color(255, 255, 255));
        // Focus ring
        b.stroke_circle_var(0.0, 0.0, 11.0, "--focus-ring-color", 2.0, "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("slider", 0, b);
    }

    // -------------------------------------------------------------
    // 6. PROGRESSBAR
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 4.0, 4.0, "--track-bg", "--rx", "--ry", Color(54, 52, 59), "--w", "--h");
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 4.0, 4.0, "--bar-bg", "--rx", "--ry", Color(208, 188, 255), "--progress-w", "--h");
        register_batch("progressbar", 0, b);
    }

    // -------------------------------------------------------------
    // 7. BADGE
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 10.0, 10.0, "--badge-bg", "--rx", "--ry", Color(74, 68, 88), "--w", "--h");
        b.draw_text_var("", 0.0, 0.0, 11.0f, "sans-serif", "--badge-fg", "--text", "--font-size", Color(230, 224, 233), 1 /* center */, 600);
        register_batch("badge", 0, b);
    }

    // -------------------------------------------------------------
    // 8. CARD
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        b.draw_card_var(
            0.0, 0.0, 0.0, 0.0,
            12.0, 12.0,
            "--card-bg", "--card-border",
            1.0, 8.0, 0.0, 0.0, 3.0,
            "--card-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 40),
            "--w", "--h"
        );
        register_batch("card", 0, b);
    }

    // -------------------------------------------------------------
    // 9. FRAME
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        b.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "--frame-bg", "--rx", "--ry", Color(29, 27, 32), "--w", "--h");
        register_batch("frame", 0, b);
    }

    // -------------------------------------------------------------
    // 10. LABEL
    // -------------------------------------------------------------
    {
        DrawBatch b;
        b.clear_var("--parent-bg");
        b.draw_text_var("", 0.0, 0.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */, 400);
        register_batch("label", 0, b);
    }

    // -------------------------------------------------------------
    // 11. ENTRY / TEXTBOX FRAME
    // -------------------------------------------------------------
    {
        DrawBatch b_normal;
        b_normal.clear_var("--parent-bg");
        b_normal.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 6.0, 6.0, "--input-bg", "--rx", "--ry", Color(29, 27, 32), "--w", "--h");
        b_normal.stroke_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 6.0, 6.0, "--input-border", 1.0, "--rx", "--ry", "--bw", Color(73, 69, 79), "--w", "--h");
        register_batch("entry", 0, b_normal);
        register_batch("textbox_frame", 0, b_normal);

        DrawBatch b_focused;
        b_focused.clear_var("--parent-bg");
        b_focused.fill_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 6.0, 6.0, "--input-bg", "--rx", "--ry", Color(29, 27, 32), "--w", "--h");
        b_focused.stroke_rounded_rect_var(0.0, 0.0, 0.0, 0.0, 6.0, 6.0, "--input-focus", 1.5, "--rx", "--ry", "--bw", Color(208, 188, 255), "--w", "--h");
        register_batch("entry", ControllerPseudoState::StateFocused, b_focused);
        register_batch("textbox_frame", ControllerPseudoState::StateFocused, b_focused);
    }

    // -------------------------------------------------------------
    // 12. TABLE COMPOSABLE BATCHES
    // -------------------------------------------------------------
    {
        // Table Header
        DrawBatch b_header;
        b_header.fill_rect_var(0.0, 0.0, 0.0, 0.0, "--header-bg", Color(37, 35, 42), "--w", "--h");
        b_header.stroke_rect_var(0.0, 0.0, 0.0, 0.0, "--header-border", 1.0, "", Color(73, 69, 79), "--w", "--h");
        b_header.draw_text_var("", 8.0, 0.0, 12.0f, "sans-serif", "--header-fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */, 600);
        register_batch("table_header", 0, b_header);

        // Table Cell
        DrawBatch b_cell;
        b_cell.fill_rect_var(0.0, 0.0, 0.0, 0.0, "--cell-bg", Color(0, 0, 0, 0), "--w", "--h");
        b_cell.draw_text_var("", 8.0, 0.0, 12.0f, "sans-serif", "--cell-fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */, 400);
        register_batch("table_cell", 0, b_cell);

        // Table Row
        DrawBatch b_row;
        b_row.fill_rect_var(0.0, 0.0, 0.0, 0.0, "--row-bg", Color(0, 0, 0, 0), "--w", "--h");
        b_row.stroke_rect_var(0.0, 0.0, 0.0, 0.0, "--row-border", 1.0, "", Color(45, 42, 50), "--w", "--h");
        register_batch("table_row", 0, b_row);
    }
}

} // namespace tkblend
