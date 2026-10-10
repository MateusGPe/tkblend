#include "draw_engine.hpp"
#include "native_controller.hpp"
#include <algorithm>
#include <cctype>

namespace tkblend {

namespace {

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
    std::string key_cls = to_lower_trim(widget_class);
    if (key_cls.empty() || w <= 0.0 || h <= 0.0) return DrawBatch();

    DrawBatch b;
    b.clear_var("--parent-bg");

    if (key_cls == "button") {
        double pad_x = 3.0;
        double pad_top = 2.0;
        double pad_bottom = 4.0;
        double bx = pad_x;
        double by = pad_top;
        double bw = std::max(4.0, w - 2.0 * pad_x);
        double bh = std::max(4.0, h - pad_top - pad_bottom);

        std::string bg_var = "--btn-bg";
        std::string fg_var = "--btn-fg";
        double shadow_blur = 3.0;
        double shadow_off_y = 1.0;

        if ((state & ControllerPseudoState::StateDisabled) != 0) {
            bg_var = "--btn-disabled-bg";
            fg_var = "--btn-disabled-fg";
            shadow_blur = 0.0;
            shadow_off_y = 0.0;
        } else if ((state & ControllerPseudoState::StateActive) != 0) {
            bg_var = "--btn-active-bg";
            fg_var = "--btn-active-fg";
            shadow_blur = 1.0;
            shadow_off_y = 0.5;
            by += 1.0;
        } else if ((state & ControllerPseudoState::StateHover) != 0) {
            bg_var = "--btn-hover-bg";
            fg_var = "--btn-hover-fg";
            shadow_blur = 4.0;
            shadow_off_y = 1.5;
        }

        b.draw_card_var(
            bx, by, bw, bh,
            8.0, 8.0,
            bg_var, "--btn-border",
            1.0, shadow_blur, 0.0, 0.0, shadow_off_y,
            "--btn-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 40)
        );

        b.draw_text_var(
            "", bx + bw / 2.0, by + bh / 2.0 + 13.0 * 0.35, 13.0f, "sans-serif",
            fg_var, "--text", "--font-size",
            Color(255, 255, 255),
            1 /* center */, 500
        );

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            b.stroke_rounded_rect_var(
                bx - 1.5, by - 1.5, bw + 3.0, bh + 3.0,
                9.5, 9.5,
                "--focus-ring-color", 2.0,
                "--rx", "--ry", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }
        return b;
    }

    if (key_cls == "switch") {
        double track_w = 40.0;
        double track_h = 22.0;
        double track_x = 4.0;
        double track_y = (h > track_h) ? (h - track_h) / 2.0 : 0.0;
        double r = track_h / 2.0;
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;
        std::string track_bg = is_checked ? "--active-bg" : "--track-bg";
        Color track_col = is_checked ? Color(208, 188, 255) : Color(54, 52, 59);

        b.fill_rounded_rect_var(track_x, track_y, track_w, track_h, r, r, track_bg, "", "", track_col);

        double thumb_r = 7.0;
        double thumb_cy = track_y + track_h / 2.0;
        double thumb_cx = is_checked ? (track_x + track_w - 11.0) : (track_x + 11.0);

        // Thumb drop shadow
        b.draw_shadow_rounded_rect_var(
            thumb_cx - thumb_r, thumb_cy - thumb_r + 0.5,
            thumb_r * 2.0, thumb_r * 2.0, thumb_r, thumb_r,
            2.0, 0.0, 0.0, 1.0,
            "--btn-shadow", "", "", "",
            Color(0, 0, 0, 50)
        );

        std::string thumb_var = is_checked ? "--thumb-active-bg" : "--thumb-bg";
        Color thumb_col = is_checked ? Color(56, 30, 114) : Color(208, 188, 255);
        b.fill_circle_var(thumb_cx, thumb_cy, thumb_r, thumb_var, "", thumb_col);

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            b.stroke_rounded_rect_var(
                track_x - 1.5, track_y - 1.5, track_w + 3.0, track_h + 3.0,
                r + 1.5, r + 1.5,
                "--focus-ring-color", 2.0, "", "", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }

        b.draw_text_var(
            "", track_x + track_w + 10.0, h / 2.0 + 13.0 * 0.35, 13.0f, "sans-serif",
            "--fg", "--text", "--font-size",
            Color(230, 224, 233), 0 /* left */
        );
        return b;
    }

    if (key_cls == "checkbox") {
        double box_size = 18.0;
        double box_x = 4.0;
        double box_y = (h > box_size) ? (h - box_size) / 2.0 : 0.0;
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;

        if (!is_checked) {
            b.fill_rounded_rect_var(box_x, box_y, box_size, box_size, 4.0, 4.0, "--box-bg", "", "", Color(37, 35, 42));
            b.stroke_rounded_rect_var(box_x, box_y, box_size, box_size, 4.0, 4.0, "--box-border", 1.5, "", "", "--border-w", Color(73, 69, 79));
        } else {
            b.fill_rounded_rect_var(box_x, box_y, box_size, box_size, 4.0, 4.0, "--active-bg", "", "", Color(208, 188, 255));
            b.stroke_rounded_rect_var(box_x, box_y, box_size, box_size, 4.0, 4.0, "--active-bg", 1.5, "", "", "--border-w", Color(208, 188, 255));
            b.draw_line_var(box_x + 4.0, box_y + 9.0, box_x + 8.0, box_y + 13.0, "--check-color", 2.0, "", Color(56, 30, 114));
            b.draw_line_var(box_x + 8.0, box_y + 13.0, box_x + 14.0, box_y + 5.0, "--check-color", 2.0, "", Color(56, 30, 114));
        }

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            b.stroke_rounded_rect_var(
                box_x - 1.5, box_y - 1.5, box_size + 3.0, box_size + 3.0,
                5.5, 5.5,
                "--focus-ring-color", 2.0, "", "", "--focus-ring-width",
                Color(208, 188, 255)
            );
        }

        b.draw_text_var(
            "", box_x + box_size + 8.0, h / 2.0 + 13.0 * 0.35, 13.0f, "sans-serif",
            "--fg", "--text", "--font-size",
            Color(230, 224, 233), 0 /* left */
        );
        return b;
    }

    if (key_cls == "radio") {
        double cr = 8.0;
        double cx = cr + 4.0;
        double cy = h / 2.0;
        bool is_checked = (state & ControllerPseudoState::StateChecked) != 0;

        if (!is_checked) {
            b.fill_circle_var(cx, cy, cr, "--radio-bg", "", Color(37, 35, 42));
            b.stroke_circle_var(cx, cy, cr, "--radio-border", 1.5, "", "", Color(73, 69, 79));
        } else {
            b.fill_circle_var(cx, cy, cr, "--radio-bg", "", Color(37, 35, 42));
            b.stroke_circle_var(cx, cy, cr, "--active-bg", 1.5, "", "", Color(208, 188, 255));
            b.fill_circle_var(cx, cy, 4.0, "--dot-color", "", Color(208, 188, 255));
        }

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            b.stroke_circle_var(cx, cy, cr + 2.5, "--focus-ring-color", 2.0, "", "--focus-ring-width", Color(208, 188, 255));
        }

        b.draw_text_var(
            "", cx + cr + 8.0, h / 2.0 + 13.0 * 0.35, 13.0f, "sans-serif",
            "--fg", "--text", "--font-size",
            Color(230, 224, 233), 0 /* left */
        );
        return b;
    }

    if (key_cls == "slider") {
        double pad = 12.0;
        double track_w = std::max(10.0, w - pad * 2.0);
        double track_h = 4.0;
        double track_y = (h > track_h) ? (h - track_h) / 2.0 : 0.0;
        double thumb_pos = 0.0;
        auto it = vars.find("--thumb-pos");
        if (it != vars.end()) {
            try { thumb_pos = std::clamp(std::stod(it->second), 0.0, 1.0); } catch (...) {}
        }

        b.fill_rounded_rect_var(pad, track_y, track_w, track_h, 2.0, 2.0, "--track-bg", "", "", Color(54, 52, 59));

        double active_w = track_w * thumb_pos;
        if (active_w > 0.0) {
            b.fill_rounded_rect_var(pad, track_y, active_w, track_h, 2.0, 2.0, "--active-track-bg", "", "", Color(208, 188, 255));
        }

        double thumb_cx = pad + active_w;
        double thumb_cy = h / 2.0;
        double thumb_r = 7.0;

        // Thumb drop shadow
        b.draw_shadow_rounded_rect_var(
            thumb_cx - thumb_r, thumb_cy - thumb_r + 0.5,
            thumb_r * 2.0, thumb_r * 2.0, thumb_r, thumb_r,
            2.0, 0.0, 0.0, 1.0,
            "--btn-shadow", "", "", "",
            Color(0, 0, 0, 50)
        );

        b.fill_circle_var(thumb_cx, thumb_cy, thumb_r, "--thumb-bg", "--thumb-r", Color(208, 188, 255));
        b.stroke_circle_var(thumb_cx, thumb_cy, thumb_r, "--thumb-border", 1.5, "--thumb-r", "", Color(255, 255, 255));

        if ((state & ControllerPseudoState::StateFocused) != 0) {
            b.stroke_circle_var(thumb_cx, thumb_cy, thumb_r + 2.5, "--focus-ring-color", 2.0, "", "--focus-ring-width", Color(208, 188, 255));
        }
        return b;
    }

    if (key_cls == "progressbar") {
        double bar_h = std::min(h, 6.0);
        double bar_y = (h > bar_h) ? (h - bar_h) / 2.0 : 0.0;
        double progress = 0.0;
        auto it = vars.find("--progress");
        if (it != vars.end()) {
            try { progress = std::clamp(std::stod(it->second), 0.0, 1.0); } catch (...) {}
        }

        b.fill_rounded_rect_var(0.0, bar_y, w, bar_h, 3.0, 3.0, "--track-bg", "--rx", "--ry", Color(54, 52, 59));
        double prog_w = w * progress;
        if (prog_w > 0.0) {
            b.fill_rounded_rect_var(0.0, bar_y, prog_w, bar_h, 3.0, 3.0, "--bar-bg", "--rx", "--ry", Color(208, 188, 255));
        }
        return b;
    }

    if (key_cls == "badge") {
        double rx = std::min(w, h) / 2.0;
        b.fill_rounded_rect_var(0.0, 0.0, w, h, rx, rx, "--badge-bg", "--rx", "--ry", Color(74, 68, 88));
        b.draw_text_var(
            "", w / 2.0, h / 2.0 + 11.0 * 0.35, 11.0f, "sans-serif",
            "--badge-fg", "--text", "--font-size",
            Color(230, 224, 233), 1 /* center */, 600
        );
        return b;
    }

    if (key_cls == "card") {
        double pad_x = 10.0;
        double pad_top = 8.0;
        double pad_bottom = 12.0;
        double cx = pad_x;
        double cy = pad_top;
        double cw = std::max(10.0, w - 2.0 * pad_x);
        double ch = std::max(10.0, h - pad_top - pad_bottom);

        b.draw_card_var(
            cx, cy, cw, ch,
            12.0, 12.0,
            "--card-bg", "--card-border",
            1.0, 8.0, 0.0, 0.0, 3.0,
            "--card-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 40)
        );
        return b;
    }

    if (key_cls == "frame") {
        b.fill_rounded_rect_var(0.0, 0.0, w, h, 0.0, 0.0, "--frame-bg", "--rx", "--ry", Color(29, 27, 32));
        return b;
    }

    if (key_cls == "label") {
        b.draw_text_var(
            "", 2.0, h / 2.0 + 13.0 * 0.35, 13.0f, "sans-serif",
            "--fg", "--text", "--font-size",
            Color(230, 224, 233), 0 /* left */, 400
        );
        return b;
    }

    if (key_cls == "entry" || key_cls == "textbox_frame") {
        std::string border_col = ((state & ControllerPseudoState::StateFocused) != 0) ? "--input-focus" : "--input-border";
        double border_w = ((state & ControllerPseudoState::StateFocused) != 0) ? 1.5 : 1.0;
        Color fallback_border = ((state & ControllerPseudoState::StateFocused) != 0) ? Color(208, 188, 255) : Color(73, 69, 79);
        b.fill_rounded_rect_var(0.0, 0.0, w, h, 6.0, 6.0, "--input-bg", "--rx", "--ry", Color(29, 27, 32));
        b.stroke_rounded_rect_var(0.0, 0.0, w, h, 6.0, 6.0, border_col, border_w, "--rx", "--ry", "--bw", fallback_border);
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
            1.0, 3.0, 0.0, 0.0, 1.0,
            "--btn-shadow",
            "--rx", "--ry", "--bw",
            Color(37, 35, 42), Color(73, 69, 79), Color(0, 0, 0, 40),
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
        b_normal.fill_rounded_rect_var(4.0, 2.0, 40.0, 22.0, 11.0, 11.0, "--track-bg", "", "", Color(54, 52, 59));
        b_normal.fill_circle_var(15.0, 13.0, 7.0, "--thumb-bg", "", Color(208, 188, 255));
        b_normal.draw_text_var("", 54.0, 17.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_normal.stroke_rounded_rect_var(2.5, 0.5, 43.0, 25.0, 12.5, 12.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
        register_batch("switch", 0, b_normal);

        // Checked
        DrawBatch b_checked;
        b_checked.clear_var("--parent-bg");
        b_checked.fill_rounded_rect_var(4.0, 2.0, 40.0, 22.0, 11.0, 11.0, "--active-bg", "", "", Color(208, 188, 255));
        b_checked.fill_circle_var(33.0, 13.0, 7.0, "--thumb-active-bg", "", Color(56, 30, 114));
        b_checked.draw_text_var("", 54.0, 17.0, 13.0f, "sans-serif", "--fg", "--text", "--font-size", Color(230, 224, 233), 0 /* left */);
        b_checked.stroke_rounded_rect_var(2.5, 0.5, 43.0, 25.0, 12.5, 12.5, "--focus-ring-color", 2.0, "", "", "--focus-ring-width", Color(0, 0, 0, 0));
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
