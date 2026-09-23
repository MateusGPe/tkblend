#include "gradient.hpp"
#include <algorithm>

namespace tkblend {

Gradient Gradient::create_linear(double x0, double y0, double x1, double y1) {
    Gradient g;
    g.type = Type::Linear;
    g.x0 = x0; g.y0 = y0;
    g.x1 = x1; g.y1 = y1;
    return g;
}

Gradient Gradient::create_radial(double x0, double y0, double r0, double x1, double y1, double r1) {
    Gradient g;
    g.type = Type::Radial;
    g.x0 = x0; g.y0 = y0; g.r0 = r0;
    g.x1 = x1; g.y1 = y1; g.r1 = r1;
    return g;
}

void Gradient::add_stop(double offset, const Color& color) {
    stops.emplace_back(std::clamp(offset, 0.0, 1.0), color);
}

void Gradient::set_extend_mode(int mode) {
    extend_mode = static_cast<BLExtendMode>(mode);
}

BLGradient Gradient::to_bl_gradient() const {
    BLGradient bl_g;
    if (type == Type::Linear) {
        bl_g = BLGradient(BLLinearGradientValues(x0, y0, x1, y1));
    } else {
        bl_g = BLGradient(BLRadialGradientValues(x0, y0, r0, x1, y1, r1));
    }
    bl_g.set_extend_mode(extend_mode);
    for (const auto& [offset, color] : stops) {
        bl_g.add_stop(offset, color.to_bl_rgba32());
    }
    return bl_g;
}

} // namespace tkblend
