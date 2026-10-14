#include "compiled_draw_batch.hpp"
#include "style_engine.hpp"
#include "fnv1a.hpp"
#include "string_utils.hpp"
#include <optional>
#include <algorithm>

namespace tkblend {

namespace {

static constexpr std::optional<ScalarSlot> match_scalar_slot(std::string_view raw_var) noexcept {
    if (raw_var.empty()) return std::nullopt;
    std::string_view s = extract_var_view(raw_var);

    switch (fnv1a64(s)) {
        case "hover-t"_hash:           return SLOT_HOVER_T;
        case "press-t"_hash:           return SLOT_PRESS_T;
        case "focus-t"_hash:           return SLOT_FOCUS_T;
        case "w"_hash:
        case "width"_hash:             return SLOT_WIDTH;
        case "h"_hash:
        case "height"_hash:            return SLOT_HEIGHT;
        case "active-w"_hash:          return SLOT_ACTIVE_W;
        case "thumb-x"_hash:           return SLOT_THUMB_X;
        case "thumb-y"_hash:           return SLOT_THUMB_Y;
        case "progress-w"_hash:        return SLOT_PROGRESS_W;
        case "focus-ring-width"_hash:  return SLOT_FOCUS_RING_W;
        case "text-x"_hash:            return SLOT_TEXT_X;
        case "text-y"_hash:            return SLOT_TEXT_Y;
        case "w_fr"_hash:              return SLOT_W_FR;
        case "h_fr"_hash:              return SLOT_H_FR;
        default:                       return std::nullopt;
    }
}

static constexpr std::optional<ColorSlot> match_color_slot(std::string_view raw_var) noexcept {
    if (raw_var.empty()) return std::nullopt;
    std::string_view s = extract_var_view(raw_var);

    switch (fnv1a64(s)) {
        case "parent-bg"_hash: return SLOT_COLOR_PARENT_BG;
        case "accent"_hash:    return SLOT_COLOR_ACCENT;
        default:               return std::nullopt;
    }
}

static const std::string* lookup_local_var(
    const std::unordered_map<std::string, std::string>& vars,
    std::string_view key
) noexcept {
    // 1. Direct search
    auto it = vars.find(std::string(key));
    if (it != vars.end()) return &it->second;

    // 2. Try stripped / prepended prefix
    if (key.starts_with("--")) {
        auto it2 = vars.find(std::string(key.substr(2)));
        if (it2 != vars.end()) return &it2->second;
    } else {
        std::string with_dash = "--";
        with_dash.append(key);
        auto it3 = vars.find(with_dash);
        if (it3 != vars.end()) return &it3->second;
    }
    return nullptr;
}

} // anonymous namespace

std::shared_ptr<CompiledDrawBatch> DrawBatchCompiler::compile(
    const DrawBatch& batch,
    const std::unordered_map<std::string, std::string>* local_vars
) {
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
                    bool resolved_local = false;
                    if (local_vars) {
                        const std::string* val = lookup_local_var(*local_vars, op.d_vars[i]);
                        if (val && !val->empty()) {
                            try {
                                size_t idx = 0;
                                cop.d[i] = std::stod(*val, &idx);
                                resolved_local = true;
                            } catch (...) {}
                        }
                    }
                    if (!resolved_local) {
                        cop.d[i] = se.resolve_scalar(op.d_vars[i], op.d[i]);
                    }
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
                bool resolved_local = false;
                if (local_vars) {
                    const std::string* val = lookup_local_var(*local_vars, op.c1_var);
                    if (val && !val->empty()) {
                        cop.c1 = se.resolve_color(*val);
                        resolved_local = true;
                    }
                }
                if (!resolved_local) {
                    cop.c1 = se.resolve_color_var(op.c1_var, op.c1);
                }
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
                bool resolved_local = false;
                if (local_vars) {
                    const std::string* val = lookup_local_var(*local_vars, op.c2_var);
                    if (val && !val->empty()) {
                        cop.c2 = se.resolve_color(*val);
                        resolved_local = true;
                    }
                }
                if (!resolved_local) {
                    cop.c2 = se.resolve_color_var(op.c2_var, op.c2);
                }
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
                bool resolved_local = false;
                if (local_vars) {
                    const std::string* val = lookup_local_var(*local_vars, op.c3_var);
                    if (val && !val->empty()) {
                        cop.c3 = se.resolve_color(*val);
                        resolved_local = true;
                    }
                }
                if (!resolved_local) {
                    cop.c3 = se.resolve_color_var(op.c3_var, op.c3);
                }
            }
        }

        // Resolve String
        std::string text = op.str;
        if (!op.str_var.empty()) {
            if (local_vars) {
                const std::string* val = lookup_local_var(*local_vars, op.str_var);
                if (val && !val->empty()) {
                    text = *val;
                }
            }
            if (text.empty()) {
                text = se.resolve_string(op.str_var, op.str);
            }
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
