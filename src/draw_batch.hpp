#pragma once

#include "color.hpp"
#include <vector>
#include <string>
#include <cstddef>

namespace tkblend {

// Command Batch / Display List
enum class DrawOpType {
    Clear,
    FillRect, StrokeRect,
    FillRoundedRect, StrokeRoundedRect,
    FillCircle, StrokeCircle,
    FillEllipse, StrokeEllipse,
    DrawLine,
    DrawText,
    DrawShadowRoundedRect,
    DrawCard,
    Save, Restore, Translate, Scale, Rotate,
    ClipRect, ClipRoundedRect, ResetClip
};

struct DrawOp {
    DrawOpType type;
    double d[8] = {0};
    Color c1;
    Color c2;
    std::string str;
    int i1 = 0, i2 = 0, i3 = 0;
};

class DrawBatch {
public:
    std::vector<DrawOp> ops;

    void clear(const Color& c);
    void fill_rect(double x, double y, double w, double h, const Color& c);
    void stroke_rect(double x, double y, double w, double h, const Color& c, double stroke_width = 1.0);
    void fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c);
    void stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c, double stroke_width = 1.0);
    void fill_circle(double cx, double cy, double r, const Color& c);
    void stroke_circle(double cx, double cy, double r, const Color& c, double stroke_width = 1.0);
    void draw_line(double x1, double y1, double x2, double y2, const Color& c, double stroke_width = 1.0);
    void draw_text(const std::string& text, double x, double y, float font_size, const std::string& font_family, const Color& c, int align = 0, int weight = 400, bool italic = false);
    void draw_shadow_rounded_rect(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const Color& shadow_color);
    void draw_card(double x, double y, double w, double h, double rx, double ry, const Color& bg, const Color& border, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const Color& shadow_col);
    void save();
    void restore();
    void translate(double tx, double ty);
    void scale(double sx, double sy);
    void rotate(double rad);
    void clip_rect(double x, double y, double w, double h);
    void clip_rounded_rect(double x, double y, double w, double h, double rx, double ry);
    void reset_clip();
    void reset();
    size_t size() const { return ops.size(); }
};

} // namespace tkblend
