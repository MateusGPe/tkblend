#pragma once

#include "color.hpp"
#include <blend2d.h>
#include <vector>
#include <utility>

namespace tkblend {

// Gradient representation
class Gradient {
public:
    enum class Type { Linear, Radial };

    Type type = Type::Linear;
    // Linear coordinates: x0, y0, x1, y1
    // Radial coordinates: x0, y0, r0, x1, y1, r1
    double x0 = 0.0, y0 = 0.0;
    double x1 = 0.0, y1 = 0.0;
    double r0 = 0.0, r1 = 0.0;
    BLExtendMode extend_mode = BL_EXTEND_MODE_PAD;

    std::vector<std::pair<double, Color>> stops;

    static Gradient create_linear(double x0, double y0, double x1, double y1);
    static Gradient create_radial(double x0, double y0, double r0, double x1, double y1, double r1);

    void add_stop(double offset, const Color& color);
    void set_extend_mode(int mode);
    BLGradient to_bl_gradient() const;
};

} // namespace tkblend
