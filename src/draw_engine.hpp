#pragma once

#include "draw_batch.hpp"
#include <string>
#include <unordered_map>
#include <mutex>
#include <vector>
#include <cstdint>
#include <optional>

namespace tkblend {

class DrawEngine {
public:
    static DrawEngine& instance();

    // Register a draw batch for a widget class and state mask
    // state_mask = 0 is the base/default batch for that class.
    void register_batch(const std::string& widget_class, uint16_t state_mask, const DrawBatch& batch);

    // Unregister a batch
    void unregister_batch(const std::string& widget_class, uint16_t state_mask);

    // Look up the best matching batch for a widget class and current state bitmask.
    // Resolution order:
    // 1. Exact match for (widget_class, state)
    // 2. Best matching registered mask where (state & mask) == mask (highest popcount)
    // 3. Class default batch (widget_class, 0)
    // 4. nullptr if no batch registered for widget_class
    const DrawBatch* get_batch(const std::string& widget_class, uint16_t state = 0) const;

    bool has_batch(const std::string& widget_class, uint16_t state = 0) const;

    // Dynamically create a DrawBatch tailored to widget dimensions, geometry, and states
    DrawBatch create_control_batch(
        const std::string& widget_class,
        uint16_t state,
        double width,
        double height,
        const std::unordered_map<uint64_t, std::string>& vars
    ) const;

    DrawBatch create_control_batch(
        const std::string& widget_class,
        uint16_t state,
        double width,
        double height,
        const std::unordered_map<std::string, std::string>& vars
    ) const;

    std::vector<std::string> get_registered_classes() const;

    void clear();
    void reset_defaults();

private:
    DrawEngine();
    ~DrawEngine() = default;

    void init_default_batches();

    mutable std::recursive_mutex mutex_;

    struct Key {
        std::string widget_class;
        uint16_t state_mask;
        bool operator==(const Key& o) const {
            return widget_class == o.widget_class && state_mask == o.state_mask;
        }
    };
    struct KeyHash {
        std::size_t operator()(const Key& k) const {
            return std::hash<std::string>()(k.widget_class) ^ (static_cast<std::size_t>(k.state_mask) << 16);
        }
    };

    std::unordered_map<Key, DrawBatch, KeyHash> batches_;
};

} // namespace tkblend
