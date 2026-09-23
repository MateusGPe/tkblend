#include "path.hpp"

namespace tkblend {

Path& Path::move_to(double x, double y) {
    path.move_to(x, y);
    return *this;
}

Path& Path::line_to(double x, double y) {
    path.line_to(x, y);
    return *this;
}

Path& Path::quad_to(double x1, double y1, double x2, double y2) {
    path.quad_to(x1, y1, x2, y2);
    return *this;
}

Path& Path::cubic_to(double x1, double y1, double x2, double y2, double x3, double y3) {
    path.cubic_to(x1, y1, x2, y2, x3, y3);
    return *this;
}

Path& Path::arc_to(double cx, double cy, double rx, double ry, double start_angle, double sweep_angle) {
    path.arc_to(cx, cy, rx, ry, start_angle, sweep_angle);
    return *this;
}

Path& Path::add_rect(double x, double y, double w, double h) {
    path.add_rect(BLRect(x, y, w, h));
    return *this;
}

Path& Path::add_rounded_rect(double x, double y, double w, double h, double rx, double ry) {
    path.add_round_rect(BLRoundRect(x, y, w, h, rx, ry));
    return *this;
}

Path& Path::add_circle(double cx, double cy, double r) {
    path.add_circle(BLCircle(cx, cy, r));
    return *this;
}

Path& Path::add_ellipse(double cx, double cy, double rx, double ry) {
    path.add_ellipse(BLEllipse(cx, cy, rx, ry));
    return *this;
}

Path& Path::close() {
    path.close();
    return *this;
}

Path& Path::clear() {
    path.clear();
    return *this;
}

Path& Path::reset() {
    path.reset();
    return *this;
}

} // namespace tkblend
