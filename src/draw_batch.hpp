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
    double d[12] = {0};
    Color c1;
    Color c2;
    Color c3;
    std::string str;
    int i1 = 0, i2 = 0, i3 = 0;

    // Dynamic variable bindings
    std::string c1_var;
    std::string c2_var;
    std::string c3_var;
    std::string str_var;
    std::string d_vars[12];
};

class DrawBatch {
public:
    std::vector<DrawOp> ops;

    void clear(const Color& c);
    void clear_var(const std::string& c_var, const Color& fallback = Color(0, 0, 0, 0));

    void fill_rect(double x, double y, double w, double h, const Color& c);
    void fill_rect_var(double x, double y, double w, double h, const std::string& c_var, const Color& fallback = Color(0, 0, 0, 255));

    void stroke_rect(double x, double y, double w, double h, const Color& c, double stroke_width = 1.0);
    void stroke_rect_var(double x, double y, double w, double h, const std::string& c_var, double stroke_width = 1.0, const std::string& sw_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c);
    void fill_rounded_rect_var(double x, double y, double w, double h, double rx, double ry, const std::string& c_var, const std::string& rx_var = "", const std::string& ry_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c, double stroke_width = 1.0);
    void stroke_rounded_rect_var(double x, double y, double w, double h, double rx, double ry, const std::string& c_var, double stroke_width = 1.0, const std::string& rx_var = "", const std::string& ry_var = "", const std::string& sw_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void fill_circle(double cx, double cy, double r, const Color& c);
    void fill_circle_var(double cx, double cy, double r, const std::string& c_var, const std::string& r_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void stroke_circle(double cx, double cy, double r, const Color& c, double stroke_width = 1.0);
    void stroke_circle_var(double cx, double cy, double r, const std::string& c_var, double stroke_width = 1.0, const std::string& r_var = "", const std::string& sw_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void draw_line(double x1, double y1, double x2, double y2, const Color& c, double stroke_width = 1.0);
    void draw_line_var(double x1, double y1, double x2, double y2, const std::string& c_var, double stroke_width = 1.0, const std::string& sw_var = "", const Color& fallback = Color(0, 0, 0, 255));

    void draw_text(const std::string& text, double x, double y, float font_size, const std::string& font_family, const Color& c, int align = 0, int weight = 400, bool italic = false);
    void draw_text_var(const std::string& text, double x, double y, float font_size, const std::string& font_family, const std::string& c_var, const std::string& text_var = "", const std::string& size_var = "", const Color& fallback = Color(255, 255, 255, 255), int align = 0, int weight = 400, bool italic = false);

    void draw_shadow_rounded_rect(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const Color& shadow_color);
    void draw_shadow_rounded_rect_var(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const std::string& shadow_color_var, const std::string& rx_var = "", const std::string& ry_var = "", const std::string& blur_var = "", const Color& fallback = Color(0, 0, 0, 30));

    void draw_card(double x, double y, double w, double h, double rx, double ry, const Color& bg, const Color& border, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const Color& shadow_col);
    void draw_card_var(double x, double y, double w, double h, double rx, double ry, const std::string& bg_var, const std::string& border_var, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const std::string& shadow_var, const std::string& rx_var = "", const std::string& ry_var = "", const std::string& bw_var = "", const Color& bg_fallback = Color(255, 255, 255, 255), const Color& border_fallback = Color(200, 200, 200, 255), const Color& shadow_fallback = Color(0, 0, 0, 30));

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
