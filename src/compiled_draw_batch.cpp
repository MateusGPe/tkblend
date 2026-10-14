#include "compiled_draw_batch.hpp"
#include "style_engine.hpp"
#include <optional>
#include <algorithm>

namespace tkblend {

namespace {

static std::optional<ScalarSlot> match_scalar_slot(const std::string& raw_var) {
    if (raw_var.empty()) return std::nullopt;
    std::string s = raw_var;
    if (s.rfind("var(", 0) == 0 && s.back() == ')') {
        s = s.substr(4, s.size() - 5);
        size_t comma = s.find(',');
        if (comma != std::string::npos) s.resize(comma);
        auto first = s.find_first_not_of(" \t\n\r");
        auto last = s.find_last_not_of(" \t\n\r");
        if (first != std::string::npos) s = s.substr(first, last - first + 1);
    }
    if (s.rfind("--", 0) == 0) s = s.substr(2);

    if (s == "hover-t") return SLOT_HOVER_T;
    if (s == "press-t") return SLOT_PRESS_T;
    if (s == "focus-t") return SLOT_FOCUS_T;
    if (s == "w" || s == "width") return SLOT_WIDTH;
    if (s == "h" || s == "height") return SLOT_HEIGHT;
    if (s == "active-w") return SLOT_ACTIVE_W;
    if (s == "thumb-x") return SLOT_THUMB_X;
    if (s == "thumb-y") return SLOT_THUMB_Y;
    if (s == "progress-w") return SLOT_PROGRESS_W;
    if (s == "focus-ring-width") return SLOT_FOCUS_RING_W;
    if (s == "text-x") return SLOT_TEXT_X;
    if (s == "text-y") return SLOT_TEXT_Y;
    if (s == "w_fr") return SLOT_W_FR;
    if (s == "h_fr") return SLOT_H_FR;
    return std::nullopt;
}

static std::optional<ColorSlot> match_color_slot(const std::string& raw_var) {
    if (raw_var.empty()) return std::nullopt;
    std::string s = raw_var;
    if (s.rfind("var(", 0) == 0 && s.back() == ')') {
        s = s.substr(4, s.size() - 5);
        size_t comma = s.find(',');
        if (comma != std::string::npos) s.resize(comma);
        auto first = s.find_first_not_of(" \t\n\r");
        auto last = s.find_last_not_of(" \t\n\r");
        if (first != std::string::npos) s = s.substr(first, last - first + 1);
    }
    if (s.rfind("--", 0) == 0) s = s.substr(2);

    if (s == "parent-bg") return SLOT_COLOR_PARENT_BG;
    if (s == "accent") return SLOT_COLOR_ACCENT;
    return std::nullopt;
}

} // anonymous namespace

std::shared_ptr<CompiledDrawBatch> DrawBatchCompiler::compile(const DrawBatch& batch) {
    auto res = std::make_shared<CompiledDrawBatch>();
    res->ops.reserve(batch.ops.size());

    StyleEngine& se = StyleEngine::instance();

    for (const auto& op : batch.ops) {
        CompiledOp cop;
        cop.type = op.type;
        cop.bbox_relative = op.bbox_relative ? 1 : 0;
        cop.i1 = op.i1;
        cop.i2 = op.i2;
        cop.i3 = op.i3;
        cop.grad = op.grad;

        // Resolve scalar variables or constants
        for (int i = 0; i < 12; ++i) {
            cop.d[i] = op.d[i];
            if (!op.d_vars[i].empty()) {
                auto slot = match_scalar_slot(op.d_vars[i]);
                if (slot.has_value()) {
                    cop.reg_mask |= static_cast<uint16_t>(1 << i);
                    cop.reg_slot[i] = static_cast<uint8_t>(*slot);
                } else {
                    cop.d[i] = se.resolve_scalar(op.d_vars[i], op.d[i]);
                }
            }
        }

        // Resolve Color 1
        cop.c1 = op.c1;
        if (!op.c1_var.empty()) {
            auto slot = match_color_slot(op.c1_var);
            if (slot.has_value()) {
                cop.reg_mask |= static_cast<uint16_t>(1 << 12);
                cop.reg_color_slot[0] = static_cast<uint8_t>(*slot);
            } else {
                cop.c1 = se.resolve_color_var(op.c1_var, op.c1);
            }
        }

        // Resolve Color 2
        cop.c2 = op.c2;
        if (!op.c2_var.empty()) {
            auto slot = match_color_slot(op.c2_var);
            if (slot.has_value()) {
                cop.reg_mask |= static_cast<uint16_t>(1 << 13);
                cop.reg_color_slot[1] = static_cast<uint8_t>(*slot);
            } else {
                cop.c2 = se.resolve_color_var(op.c2_var, op.c2);
            }
        }

        // Resolve Color 3
        cop.c3 = op.c3;
        if (!op.c3_var.empty()) {
            auto slot = match_color_slot(op.c3_var);
            if (slot.has_value()) {
                cop.reg_mask |= static_cast<uint16_t>(1 << 14);
                cop.reg_color_slot[2] = static_cast<uint8_t>(*slot);
            } else {
                cop.c3 = se.resolve_color_var(op.c3_var, op.c3);
            }
        }

        // Resolve String
        std::string text = op.str;
        if (!op.str_var.empty()) {
            text = se.resolve_string(op.str_var, op.str);
        }
        if (!text.empty()) {
            cop.str_index = static_cast<uint32_t>(res->string_table.size());
            res->string_table.push_back(std::move(text));
        } else {
            cop.str_index = 0xFFFFFFFF;
        }

        res->ops.push_back(std::move(cop));
    }

    return res;
}

void CompiledDrawBatch::rebake_theme_constants() {
    if (!source_batch) return;
    auto fresh = DrawBatchCompiler::compile(*source_batch);
    ops = std::move(fresh->ops);
    string_table = std::move(fresh->string_table);
}

} // namespace tkblend
