#pragma once

#include "surface.hpp"
#include "color.hpp"
#include "viewport_controller.hpp"

#include <string>
#include <vector>
#include <unordered_set>
#include <tuple>
#include <optional>

namespace tkblend {

struct TableThemeColors {
    Color card_bg{37, 35, 42, 255};
    Color card_border{73, 69, 79, 255};
    Color fg{230, 224, 233, 255};
    Color header_bg{37, 35, 42, 255};
    Color header_fg{150, 150, 160, 255};
    Color zebra_bg{47, 45, 56, 255};
    Color hover_bg{56, 53, 66, 255};
    Color selected_bg{139, 92, 246, 255};
    Color selected_fg{255, 255, 255, 255};
    Color scrollbar_idle{73, 69, 79, 255};
    Color scrollbar_hover{139, 92, 246, 255};
};

struct TableRenderSpec {
    int width = 0;
    int height = 0;
    int row_height = 34;
    int header_height = 38;
    int scrollbar_width = 7;
    double corner_radius = 8.0;
    bool zebra_striping = true;

    double scroll_x = 0.0;
    double scroll_y = 0.0;

    int sort_column = -1;
    bool sort_ascending = true;

    int hovered_row = -1;
    bool vbar_active = false;
    bool hbar_active = false;

    std::vector<std::string> columns;
    std::vector<int> col_widths;
    std::vector<std::vector<std::string>> data;
    std::unordered_set<int> selected_rows;

    TableThemeColors colors;
};

class TableRenderEngine {
public:
    static void render_table(Surface& surf, const TableRenderSpec& spec);

    static int find_column_divider(
        double mouse_x,
        const std::vector<int>& col_widths,
        double scroll_x,
        double threshold = 4.0
    );

    static std::pair<int, int> get_cell_at(
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
    );

    static std::tuple<int, int, int, int> get_cell_bounds(
        int row_idx,
        int col_idx,
        const std::vector<int>& col_widths,
        int row_h,
        int header_h,
        double scroll_x,
        double scroll_y
    );
};

} // namespace tkblend
