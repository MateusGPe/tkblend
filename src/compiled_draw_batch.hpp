#pragma once

#include "color.hpp"
#include "gradient.hpp"
#include "draw_batch.hpp"
#include <vector>
#include <string>
#include <unordered_map>
#include <cstdint>
#include <memory>

namespace tkblend {

// Well-known scalar register slots
enum ScalarSlot : uint8_t {
    SLOT_HOVER_T = 0,
    SLOT_PRESS_T = 1,
    SLOT_FOCUS_T = 2,
    SLOT_WIDTH = 3,
    SLOT_HEIGHT = 4,
    SLOT_ACTIVE_W = 5,
    SLOT_THUMB_X = 6,
    SLOT_THUMB_Y = 7,
    SLOT_PROGRESS_W = 8,
    SLOT_FOCUS_RING_W = 9,
    SLOT_TEXT_X = 10,
    SLOT_TEXT_Y = 11,
    SLOT_W_FR = 12,
    SLOT_H_FR = 13,
    SLOT_CUSTOM_1 = 14,
    SLOT_CUSTOM_2 = 15,
    SCALAR_SLOT_COUNT = 16
};

// Well-known color register slots
enum ColorSlot : uint8_t {
    SLOT_COLOR_PARENT_BG = 0,
    SLOT_COLOR_ACCENT = 1,
    SLOT_COLOR_CUSTOM_1 = 2,
    SLOT_COLOR_CUSTOM_2 = 3,
    SLOT_COLOR_CUSTOM_3 = 4,
    SLOT_COLOR_CUSTOM_5 = 5,
    SLOT_COLOR_CUSTOM_6 = 6,
    SLOT_COLOR_CUSTOM_7 = 7,
    COLOR_SLOT_COUNT = 8
};

struct FastRegisterBank {
    float scalars[SCALAR_SLOT_COUNT] = {0.0f};
    Color colors[COLOR_SLOT_COUNT];

    void set_scalar(uint8_t slot, float val) noexcept {
        if (slot < SCALAR_SLOT_COUNT) scalars[slot] = val;
    }
    float get_scalar(uint8_t slot) const noexcept {
        return (slot < SCALAR_SLOT_COUNT) ? scalars[slot] : 0.0f;
    }

    void set_color(uint8_t slot, const Color& c) noexcept {
        if (slot < COLOR_SLOT_COUNT) colors[slot] = c;
    }
    Color get_color(uint8_t slot) const noexcept {
        return (slot < COLOR_SLOT_COUNT) ? colors[slot] : Color();
    }
};

struct CompiledOp {
    DrawOpType type{DrawOpType::Clear};
    uint8_t bbox_relative{0};
    uint16_t reg_mask{0}; // Bit 0-11: d[i] is dynamic; Bit 12: c1 dynamic; Bit 13: c2; Bit 14: c3
    uint8_t reg_slot[12]{0};
    uint8_t reg_color_slot[3]{0};
    int i1{0}, i2{0}, i3{0};
    uint32_t str_index{0xFFFFFFFF}; // Index into string table, 0xFFFFFFFF if none

    double d[12]{0.0};
    Color c1;
    Color c2;
    Color c3;
    Gradient grad;
};

class CompiledDrawBatch {
public:
    CompiledDrawBatch() = default;

    std::vector<CompiledOp> ops;
    std::vector<std::string> string_table;
    std::shared_ptr<DrawBatch> source_batch;

    size_t size() const noexcept { return ops.size(); }
    bool empty() const noexcept { return ops.empty(); }

    const std::string& get_string(uint32_t idx) const {
        static const std::string empty_str;
        if (idx < string_table.size()) {
            return string_table[idx];
        }
        return empty_str;
    }

    // Re-bake theme constants from source_batch when theme changes
    void rebake_theme_constants();
};

class DrawBatchCompiler {
public:
    static std::shared_ptr<CompiledDrawBatch> compile(
        const DrawBatch& batch,
        const std::unordered_map<uint64_t, std::string>* local_vars = nullptr
    );
};

} // namespace tkblend
