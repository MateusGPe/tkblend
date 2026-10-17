#include "table_engine.hpp"
#include <numeric>

namespace tkblend {

void TableRenderEngine::render_table(Surface& surf, const TableRenderSpec& spec) {
    int w = spec.width > 0 ? spec.width : surf.width();
    int h = spec.height > 0 ? spec.height : surf.height();
    if (w <= 4 || h <= 4) return;

    int total_content_h = static_cast<int>(spec.data.size()) * spec.row_height;
    int base_available_w = w - 4;

    int prelim_viewport_h = std::max(0, h - spec.header_height - 2);
    bool v_needed = total_content_h > prelim_viewport_h;

    int available_w = base_available_w;
    if (v_needed) {
        available_w -= (spec.scrollbar_width + 6);
    }

    int total_content_w = 0;
    for (int cw : spec.col_widths) total_content_w += cw;
    if (total_content_w == 0) total_content_w = available_w;

    bool h_needed = total_content_w > available_w;
    int viewport_h = std::max(0, h - spec.header_height - (h_needed ? (spec.scrollbar_width + 6) : 2));
    v_needed = total_content_h > viewport_h;
    if (v_needed && available_w == base_available_w) {
        available_w -= (spec.scrollbar_width + 6);
        h_needed = total_content_w > available_w;
    }

    double max_scroll_y = std::max(0.0, static_cast<double>(total_content_h - viewport_h));
    double clamped_scroll_y = std::clamp(spec.scroll_y, 0.0, max_scroll_y);

    double max_scroll_x = std::max(0.0, static_cast<double>(total_content_w - available_w));
    double clamped_scroll_x = std::clamp(spec.scroll_x, 0.0, max_scroll_x);

    // 1. Fill base card background with smooth rounded corners
    surf.fill_rounded_rect(0, 0, w, h, spec.corner_radius, spec.corner_radius, spec.colors.card_bg);

    // 2. Clip all table content to the rounded card boundary
    surf.save();
    surf.clip_rounded_rect(0, 0, w, h, spec.corner_radius, spec.corner_radius);

    // 3. Draw Header Background & Separators
    surf.fill_rect(0, 0, w, spec.header_height, spec.colors.header_bg);
    surf.draw_line(0, spec.header_height, w, spec.header_height, spec.colors.card_border, 1.0);

    // Header Columns
    surf.save();
    surf.clip_rect(0, 0, available_w, spec.header_height);

    double curr_x = -clamped_scroll_x;
    for (size_t col_idx = 0; col_idx < spec.columns.size(); ++col_idx) {
        int col_w = (col_idx < spec.col_widths.size()) ? spec.col_widths[col_idx] : 100;

        surf.save();
        surf.clip_rect(std::max(0.0, curr_x + 2.0), 0, std::max(0.0, col_w - 4.0), spec.header_height);

        std::string full_header = spec.columns[col_idx];
        if (static_cast<int>(col_idx) == spec.sort_column) {
            full_header += (spec.sort_ascending ? " ▲" : " ▼");
        }

        size_t max_h_chars = static_cast<size_t>(std::max(3.0, (col_w - 18.0) / 7.2));
        std::string display_header = (full_header.size() > max_h_chars)
            ? full_header.substr(0, max_h_chars - 1) + "…"
            : full_header;

        double ty = spec.header_height / 2.0 + 4.0;
        surf.draw_text(
            display_header,
            curr_x + 10.0,
            ty,
            11.0f,
            "sans-serif",
            spec.colors.header_fg,
            0,
            600,
            false
        );
        surf.restore();

        // Column vertical separator
        surf.draw_line(curr_x + col_w, 6, curr_x + col_w, spec.header_height - 6, spec.colors.card_border, 0.75);
        curr_x += col_w;
    }
    surf.restore(); // End header clip

    // 4. Virtualized Row Rendering
    surf.save();
    surf.clip_rect(0, spec.header_height + 1, available_w, viewport_h);

    size_t first_row = static_cast<size_t>(std::max(0.0, std::floor(clamped_scroll_y / spec.row_height)));
    size_t last_row = static_cast<size_t>(std::min(static_cast<double>(spec.data.size()),
                                                   std::ceil((clamped_scroll_y + viewport_h) / spec.row_height) + 1.0));

    for (size_t row_idx = first_row; row_idx < last_row && row_idx < spec.data.size(); ++row_idx) {
        const auto& row = spec.data[row_idx];
        double row_y = spec.header_height + row_idx * spec.row_height - clamped_scroll_y;
        bool is_selected = (spec.selected_rows.find(static_cast<int>(row_idx)) != spec.selected_rows.end());
        bool is_hovered = (spec.hovered_row == static_cast<int>(row_idx) && !is_selected);

        Color row_fill = spec.colors.card_bg;
        Color text_col = spec.colors.fg;
        if (is_selected) {
            row_fill = spec.colors.selected_bg;
            text_col = spec.colors.selected_fg;
        } else if (is_hovered) {
            row_fill = spec.colors.hover_bg;
            text_col = spec.colors.fg;
        } else if (spec.zebra_striping && (row_idx % 2 == 1)) {
            row_fill = spec.colors.zebra_bg;
            text_col = spec.colors.fg;
        }

        // Draw row background
        surf.fill_rect(0, row_y, available_w, spec.row_height, row_fill);

        // Bottom row divider
        surf.draw_line(0, row_y + spec.row_height, available_w, row_y + spec.row_height, spec.colors.card_border, 0.5);

        // Draw cell text
        double cell_x = -clamped_scroll_x;
        for (size_t col_idx = 0; col_idx < spec.col_widths.size(); ++col_idx) {
            int col_w = spec.col_widths[col_idx];
            std::string raw_val = (col_idx < row.size()) ? row[col_idx] : "";

            surf.save();
            surf.clip_rect(std::max(0.0, cell_x + 2.0), row_y, std::max(0.0, col_w - 4.0), spec.row_height);

            size_t max_chars = static_cast<size_t>(std::max(3.0, (col_w - 18.0) / 6.8));
            std::string display_val = (raw_val.size() > max_chars)
                ? raw_val.substr(0, max_chars - 1) + "…"
                : raw_val;

            double cy = row_y + spec.row_height / 2.0 + 3.5;
            surf.draw_text(
                display_val,
                cell_x + 10.0,
                cy,
                10.0f,
                "sans-serif",
                text_col,
                0,
                400,
                false
            );
            surf.restore();

            cell_x += col_w;
        }
    }
    surf.restore(); // End body clip

    // 5. Draw Pure Blend2D Scrollbars
    if (v_needed) {
        double track_len = std::max(10.0, static_cast<double>(viewport_h - 8.0));
        double thumb_len = std::clamp(viewport_h * (static_cast<double>(viewport_h) / total_content_h), 24.0, track_len);
        double max_s = std::max(1.0, static_cast<double>(total_content_h - viewport_h));
        double progress = std::clamp(clamped_scroll_y / max_s, 0.0, 1.0);
        double thumb_offset = progress * (track_len - thumb_len);

        double vx = w - spec.scrollbar_width - 3.0;
        double vy = spec.header_height + 4.0 + thumb_offset;
        double vw = spec.scrollbar_width;
        double vh = thumb_len;

        Color bar_color = spec.vbar_active ? spec.colors.scrollbar_hover : spec.colors.scrollbar_idle;
        surf.fill_rounded_rect(vx, vy, vw, vh, vw / 2.0, vw / 2.0, bar_color);
    }

    if (h_needed) {
        double track_len = std::max(10.0, static_cast<double>(available_w - 8.0));
        double thumb_len = std::clamp(available_w * (static_cast<double>(available_w) / total_content_w), 24.0, track_len);
        double max_s = std::max(1.0, static_cast<double>(total_content_w - available_w));
        double progress = std::clamp(clamped_scroll_x / max_s, 0.0, 1.0);
        double thumb_offset = progress * (track_len - thumb_len);

        double hx = 4.0 + thumb_offset;
        double hy = h - spec.scrollbar_width - 3.0;
        double hw = thumb_len;
        double hh = spec.scrollbar_width;

        Color bar_color = spec.hbar_active ? spec.colors.scrollbar_hover : spec.colors.scrollbar_idle;
        surf.fill_rounded_rect(hx, hy, hw, hh, hh / 2.0, hh / 2.0, bar_color);
    }

    surf.restore(); // End card clip

    // 6. Stroke outer rounded card border
    surf.stroke_rounded_rect(0.5, 0.5, w - 1.0, h - 1.0, spec.corner_radius, spec.corner_radius, spec.colors.card_border, 1.0);
}

int TableRenderEngine::find_column_divider(
    double mouse_x,
    const std::vector<int>& col_widths,
    double scroll_x,
    double threshold
) {
    if (col_widths.size() <= 1) return -1;
    double curr_x = -scroll_x;
    for (size_t col_idx = 0; col_idx + 1 < col_widths.size(); ++col_idx) {
        curr_x += col_widths[col_idx];
        if (std::abs(mouse_x - curr_x) <= threshold) {
            return static_cast<int>(col_idx);
        }
    }
    return -1;
}

std::pair<int, int> TableRenderEngine::get_cell_at(
    double x,
    double y,
    int w,
    int h,
    const std::vector<int>& col_widths,
    size_t row_count,
    int row_h,
    int header_h,
    double scroll_x,
    double scroll_y,
    int scrollbar_w
) {
    int total_h = static_cast<int>(row_count) * row_h;
    bool v_needed = total_h > (h - header_h);
    int available_w = w - (v_needed ? (scrollbar_w + 6) : 0);

    if (x < 0 || x > available_w || y < header_h || y > h) {
        return {-1, -1};
    }

    int row_idx = static_cast<int>((y - header_h + scroll_y) / row_h);
    if (row_idx < 0 || static_cast<size_t>(row_idx) >= row_count) {
        return {-1, -1};
    }

    double curr_x = -scroll_x;
    for (size_t col_idx = 0; col_idx < col_widths.size(); ++col_idx) {
        double next_x = curr_x + col_widths[col_idx];
        if (x >= curr_x && x < next_x) {
            return {row_idx, static_cast<int>(col_idx)};
        }
        curr_x = next_x;
    }

    return {-1, -1};
}

std::tuple<int, int, int, int> TableRenderEngine::get_cell_bounds(
    int row_idx,
    int col_idx,
    const std::vector<int>& col_widths,
    int row_h,
    int header_h,
    double scroll_x,
    double scroll_y
) {
    if (col_idx < 0 || static_cast<size_t>(col_idx) >= col_widths.size()) {
        return {-1, -1, 0, 0};
    }

    int cell_x = static_cast<int>(-scroll_x);
    for (int i = 0; i < col_idx; ++i) {
        cell_x += col_widths[i];
    }
    int cell_w = col_widths[col_idx];
    int cell_y = static_cast<int>(header_h + row_idx * row_h - scroll_y);
    return {cell_x, cell_y, cell_w, row_h};
}

} // namespace tkblend
