#pragma once

#include <blend2d.h>

namespace tkblend {

// Vector Path representation
class Path {
public:
    BLPath path;

    Path() = default;

    Path& move_to(double x, double y);
    Path& line_to(double x, double y);
    Path& quad_to(double x1, double y1, double x2, double y2);
    Path& cubic_to(double x1, double y1, double x2, double y2, double x3, double y3);
    Path& arc_to(double cx, double cy, double rx, double ry, double start_angle, double sweep_angle);
    Path& add_rect(double x, double y, double w, double h);
    Path& add_rounded_rect(double x, double y, double w, double h, double rx, double ry);
    Path& add_circle(double cx, double cy, double r);
    Path& add_ellipse(double cx, double cy, double rx, double ry);
    Path& close();
    Path& clear();
    Path& reset();
};

} // namespace tkblend
