#include "draw_batch.hpp"
#include <utility>

namespace tkblend {

void DrawBatch::clear(const Color& c) {
    DrawOp op; op.type = DrawOpType::Clear; op.c1 = c; ops.push_back(std::move(op));
}

void DrawBatch::fill_rect(double x, double y, double w, double h, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::stroke_rect(double x, double y, double w, double h, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::fill_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::stroke_rounded_rect(double x, double y, double w, double h, double rx, double ry, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; op.d[6]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::fill_circle(double cx, double cy, double r, const Color& c) {
    DrawOp op; op.type = DrawOpType::FillCircle; op.d[0]=cx; op.d[1]=cy; op.d[2]=r; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::stroke_circle(double cx, double cy, double r, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::StrokeCircle; op.d[0]=cx; op.d[1]=cy; op.d[2]=r; op.d[3]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::draw_line(double x1, double y1, double x2, double y2, const Color& c, double stroke_width) {
    DrawOp op; op.type = DrawOpType::DrawLine; op.d[0]=x1; op.d[1]=y1; op.d[2]=x2; op.d[3]=y2; op.d[4]=stroke_width; op.c1=c; ops.push_back(std::move(op));
}

void DrawBatch::draw_text(const std::string& text, double x, double y, float font_size, const std::string& font_family, const Color& c, int align, int weight, bool italic) {
    DrawOp op; op.type = DrawOpType::DrawText; op.str = text; op.d[0]=x; op.d[1]=y; op.d[2]=font_size; op.c1=c; op.i1=align; op.i2=weight; op.i3=italic ? 1 : 0;
    ops.push_back(std::move(op));
}

void DrawBatch::draw_shadow_rounded_rect(double x, double y, double w, double h, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, const Color& shadow_color) {
    DrawOp op; op.type = DrawOpType::DrawShadowRoundedRect;
    op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry;
    op.d[6]=blur_radius; op.d[7]=spread; op.d[8]=offset_x; op.d[9]=offset_y;
    op.c1=shadow_color; ops.push_back(std::move(op));
}

void DrawBatch::draw_card(double x, double y, double w, double h, double rx, double ry, const Color& bg, const Color& border, double border_w, double shadow_blur, double shadow_spread, double shadow_ox, double shadow_oy, const Color& shadow_col) {
    DrawOp op; op.type = DrawOpType::DrawCard;
    op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry;
    op.d[6]=border_w; op.d[7]=shadow_blur; op.d[8]=shadow_spread; op.d[9]=shadow_ox; op.d[10]=shadow_oy;
    op.c1=bg; op.c2=border; op.c3=shadow_col; ops.push_back(std::move(op));
}

void DrawBatch::save() { DrawOp op; op.type = DrawOpType::Save; ops.push_back(std::move(op)); }
void DrawBatch::restore() { DrawOp op; op.type = DrawOpType::Restore; ops.push_back(std::move(op)); }
void DrawBatch::translate(double tx, double ty) { DrawOp op; op.type = DrawOpType::Translate; op.d[0]=tx; op.d[1]=ty; ops.push_back(std::move(op)); }
void DrawBatch::scale(double sx, double sy) { DrawOp op; op.type = DrawOpType::Scale; op.d[0]=sx; op.d[1]=sy; ops.push_back(std::move(op)); }
void DrawBatch::rotate(double rad) { DrawOp op; op.type = DrawOpType::Rotate; op.d[0]=rad; ops.push_back(std::move(op)); }
void DrawBatch::clip_rect(double x, double y, double w, double h) { DrawOp op; op.type = DrawOpType::ClipRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; ops.push_back(std::move(op)); }
void DrawBatch::clip_rounded_rect(double x, double y, double w, double h, double rx, double ry) { DrawOp op; op.type = DrawOpType::ClipRoundedRect; op.d[0]=x; op.d[1]=y; op.d[2]=w; op.d[3]=h; op.d[4]=rx; op.d[5]=ry; ops.push_back(std::move(op)); }
void DrawBatch::reset_clip() { DrawOp op; op.type = DrawOpType::ResetClip; ops.push_back(std::move(op)); }
void DrawBatch::reset() { ops.clear(); }

} // namespace tkblend
