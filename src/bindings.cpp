#include "tkblend.hpp"
#include "style_engine.hpp"
#include "surface_registry.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/optional.h>

#include <sstream>
#include <optional>
#include <stdexcept>
#include <mutex>

namespace nb = nanobind;

namespace tkblend {

namespace {

void bind_constants(nb::module_& m) {
    // Blend composition operators
    m.attr("COMP_OP_SRC_OVER") = static_cast<int>(BL_COMP_OP_SRC_OVER);
    m.attr("COMP_OP_SRC_COPY") = static_cast<int>(BL_COMP_OP_SRC_COPY);
    m.attr("COMP_OP_SRC_IN")   = static_cast<int>(BL_COMP_OP_SRC_IN);
    m.attr("COMP_OP_SRC_OUT")  = static_cast<int>(BL_COMP_OP_SRC_OUT);
    m.attr("COMP_OP_SRC_ATOP") = static_cast<int>(BL_COMP_OP_SRC_ATOP);
    m.attr("COMP_OP_DST_OVER") = static_cast<int>(BL_COMP_OP_DST_OVER);
    m.attr("COMP_OP_DST_IN")   = static_cast<int>(BL_COMP_OP_DST_IN);
    m.attr("COMP_OP_DST_OUT")  = static_cast<int>(BL_COMP_OP_DST_OUT);
    m.attr("COMP_OP_DST_ATOP") = static_cast<int>(BL_COMP_OP_DST_ATOP);
    m.attr("COMP_OP_XOR")      = static_cast<int>(BL_COMP_OP_XOR);
    m.attr("COMP_OP_CLEAR")    = static_cast<int>(BL_COMP_OP_CLEAR);
    m.attr("COMP_OP_PLUS")     = static_cast<int>(BL_COMP_OP_PLUS);
    m.attr("COMP_OP_MULTIPLY") = static_cast<int>(BL_COMP_OP_MULTIPLY);
    m.attr("COMP_OP_SCREEN")   = static_cast<int>(BL_COMP_OP_SCREEN);
    m.attr("COMP_OP_OVERLAY")  = static_cast<int>(BL_COMP_OP_OVERLAY);
    m.attr("COMP_OP_DARKEN")   = static_cast<int>(BL_COMP_OP_DARKEN);
    m.attr("COMP_OP_LIGHTEN")  = static_cast<int>(BL_COMP_OP_LIGHTEN);

    // Gradient extend modes
    m.attr("EXTEND_PAD")     = static_cast<int>(BL_EXTEND_MODE_PAD);
    m.attr("EXTEND_REPEAT")  = static_cast<int>(BL_EXTEND_MODE_REPEAT);
    m.attr("EXTEND_REFLECT") = static_cast<int>(BL_EXTEND_MODE_REFLECT);
}

void bind_color(nb::module_& m) {
    nb::class_<Color>(m, "Color")
        .def(nb::init<uint8_t, uint8_t, uint8_t, uint8_t>(),
             nb::arg("r") = 0, nb::arg("g") = 0, nb::arg("b") = 0, nb::arg("a") = 255)
        .def_rw("r", &Color::r)
        .def_rw("g", &Color::g)
        .def_rw("b", &Color::b)
        .def_rw("a", &Color::a)
        .def_static("from_hex", &Color::from_hex, nb::arg("hex"))
        .def_static("from_u32", &Color::from_u32, nb::arg("argb"))
        .def("to_u32", &Color::to_u32)
        .def("lighten", &Color::lighten, nb::arg("factor"))
        .def("darken", &Color::darken, nb::arg("factor"))
        .def("lerp", &Color::lerp, nb::arg("other"), nb::arg("t"))
        .def("with_alpha", &Color::with_alpha, nb::arg("new_a"))
        .def("with_alpha_f", &Color::with_alpha_f, nb::arg("new_a"))
        .def("__repr__", [](const Color& c) {
            std::ostringstream ss;
            ss << "Color(r=" << static_cast<int>(c.r) << ", g=" << static_cast<int>(c.g)
               << ", b=" << static_cast<int>(c.b) << ", a=" << static_cast<int>(c.a) << ")";
            return ss.str();
        });
}

void bind_animation(nb::module_& m) {
    nb::enum_<EasingType>(m, "EasingType", nb::is_arithmetic())
        .value("Linear", EasingType::Linear)
        .value("QuadIn", EasingType::QuadIn)
        .value("QuadOut", EasingType::QuadOut)
        .value("QuadInOut", EasingType::QuadInOut)
        .value("CubicIn", EasingType::CubicIn)
        .value("CubicOut", EasingType::CubicOut)
        .value("CubicInOut", EasingType::CubicInOut)
        .value("QuartIn", EasingType::QuartIn)
        .value("QuartOut", EasingType::QuartOut)
        .value("QuartInOut", EasingType::QuartInOut)
        .value("SineIn", EasingType::SineIn)
        .value("SineOut", EasingType::SineOut)
        .value("SineInOut", EasingType::SineInOut)
        .value("ExpoIn", EasingType::ExpoIn)
        .value("ExpoOut", EasingType::ExpoOut)
        .value("ExpoInOut", EasingType::ExpoInOut)
        .value("CircIn", EasingType::CircIn)
        .value("CircOut", EasingType::CircOut)
        .value("CircInOut", EasingType::CircInOut)
        .value("ElasticIn", EasingType::ElasticIn)
        .value("ElasticOut", EasingType::ElasticOut)
        .value("ElasticInOut", EasingType::ElasticInOut)
        .value("BackIn", EasingType::BackIn)
        .value("BackOut", EasingType::BackOut)
        .value("BackInOut", EasingType::BackInOut)
        .value("BounceIn", EasingType::BounceIn)
        .value("BounceOut", EasingType::BounceOut)
        .value("BounceInOut", EasingType::BounceInOut)
        .export_values();

    m.def("ease", [](nb::object easing_type, double t) -> double {
        if (nb::isinstance<EasingType>(easing_type)) {
            return ease(static_cast<int>(nb::cast<EasingType>(easing_type)), t);
        }
        return ease(nb::cast<int>(easing_type), t);
    }, nb::arg("easing_type"), nb::arg("t"));

    m.def("spring", &spring,
          nb::arg("t"), nb::arg("mass") = 1.0, nb::arg("stiffness") = 100.0, nb::arg("damping") = 10.0);
}

void bind_text_metrics(nb::module_& m) {
    nb::class_<TextMetrics>(m, "TextMetrics")
        .def_ro("width", &TextMetrics::width)
        .def_ro("height", &TextMetrics::height)
        .def_ro("ascent", &TextMetrics::ascent)
        .def_ro("descent", &TextMetrics::descent)
        .def_ro("advance_x", &TextMetrics::advance_x)
        .def("__repr__", [](const TextMetrics& tm) {
            std::ostringstream ss;
            ss << "TextMetrics(width=" << tm.width << ", height=" << tm.height
               << ", ascent=" << tm.ascent << ", descent=" << tm.descent
               << ", advance_x=" << tm.advance_x << ")";
            return ss.str();
        });
}

void bind_draw_batch(nb::module_& m) {
    nb::class_<DrawBatch>(m, "DrawBatch")
        .def(nb::init<>())
        .def("clear", &DrawBatch::clear, nb::arg("color"))
        .def("fill_rect", &DrawBatch::fill_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"))
        .def("stroke_rect", &DrawBatch::stroke_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_rounded_rect", &DrawBatch::fill_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("stroke_rounded_rect", &DrawBatch::stroke_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_circle", &DrawBatch::fill_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"))
        .def("stroke_circle", &DrawBatch::stroke_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_line", &DrawBatch::draw_line, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_text", [](DrawBatch& b,
                             const std::string& text, double x, double y,
                             float font_size, const std::string& font_family,
                             std::optional<Color> color, int align,
                             int weight, bool italic) {
            Color col = color.value_or(Color(255, 255, 255, 255));
            b.draw_text(text, x, y, font_size, font_family, col, align, weight, italic);
        },
             nb::arg("text"), nb::arg("x"), nb::arg("y"),
             nb::arg("font_size") = 14.0f, nb::arg("font_family") = "default",
             nb::arg("color") = nb::none(), nb::arg("align") = 0,
             nb::arg("weight") = 400, nb::arg("italic") = false)
        .def("draw_shadow_rounded_rect", [](DrawBatch& b,
                                            double x, double y, double w, double h,
                                            double rx, double ry,
                                            double blur_radius, double spread,
                                            double offset_x, double offset_y,
                                            std::optional<Color> shadow_color) {
            Color sc = shadow_color.value_or(Color(0, 0, 0, 128));
            b.draw_shadow_rounded_rect(x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"), nb::arg("blur_radius"),
             nb::arg("spread") = 0.0, nb::arg("offset_x") = 0.0,
             nb::arg("offset_y") = 0.0, nb::arg("shadow_color") = nb::none())
        .def("draw_card", [](DrawBatch& b,
                             double x, double y, double w, double h,
                             double rx, double ry,
                             const Color& bg_color,
                             std::optional<Color> border_color,
                             double border_width,
                             double shadow_blur,
                             double shadow_spread,
                             double shadow_offset_x,
                             double shadow_offset_y,
                             std::optional<Color> shadow_color) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color sc = shadow_color.value_or(Color(0, 0, 0, 0));
            b.draw_card(x, y, w, h, rx, ry, bg_color, bc, border_width,
                        shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_spread") = 0.0,
             nb::arg("shadow_offset_x") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none())
        .def("save", &DrawBatch::save)
        .def("restore", &DrawBatch::restore)
        .def("translate", &DrawBatch::translate, nb::arg("tx"), nb::arg("ty"))
        .def("scale", &DrawBatch::scale, nb::arg("sx"), nb::arg("sy"))
        .def("rotate", &DrawBatch::rotate, nb::arg("rad"))
        .def("clip_rect", &DrawBatch::clip_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("clip_rounded_rect", &DrawBatch::clip_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"))
        .def("reset_clip", &DrawBatch::reset_clip)
        .def("reset", &DrawBatch::reset)
        .def("__len__", &DrawBatch::size);
}

void bind_gradient(nb::module_& m) {
    nb::class_<Gradient>(m, "Gradient")
        .def_static("linear", &Gradient::create_linear,
                    nb::arg("x0"), nb::arg("y0"), nb::arg("x1"), nb::arg("y1"))
        .def_static("radial", &Gradient::create_radial,
                    nb::arg("x0"), nb::arg("y0"), nb::arg("r0"),
                    nb::arg("x1"), nb::arg("y1"), nb::arg("r1"))
        .def("add_stop", &Gradient::add_stop, nb::arg("offset"), nb::arg("color"))
        .def("set_extend_mode", &Gradient::set_extend_mode, nb::arg("mode"));
}

void bind_path(nb::module_& m) {
    nb::class_<Path>(m, "Path")
        .def(nb::init<>())
        .def("move_to", &Path::move_to, nb::arg("x"), nb::arg("y"), nb::rv_policy::reference_internal)
        .def("line_to", &Path::line_to, nb::arg("x"), nb::arg("y"), nb::rv_policy::reference_internal)
        .def("quad_to", &Path::quad_to, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::rv_policy::reference_internal)
        .def("cubic_to", &Path::cubic_to, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("x3"), nb::arg("y3"), nb::rv_policy::reference_internal)
        .def("arc_to", &Path::arc_to, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("start_angle"), nb::arg("sweep_angle"), nb::rv_policy::reference_internal)
        .def("add_rect", &Path::add_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::rv_policy::reference_internal)
        .def("add_rounded_rect", &Path::add_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::rv_policy::reference_internal)
        .def("add_circle", &Path::add_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::rv_policy::reference_internal)
        .def("add_ellipse", &Path::add_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::rv_policy::reference_internal)
        .def("close", &Path::close, nb::rv_policy::reference_internal)
        .def("clear", &Path::clear, nb::rv_policy::reference_internal)
        .def("reset", &Path::reset, nb::rv_policy::reference_internal);
}

void bind_font_manager(nb::module_& m) {
    m.def("load_font_face", [](const std::string& name, const std::string& filepath) {
        return FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("load_font", [](const std::string& name, const std::string& filepath) {
        return FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("register_font", [](const std::string& name, const std::string& filepath) {
        return FontManager::instance().load_font_face(name, filepath);
    }, nb::arg("name"), nb::arg("filepath"));

    m.def("find_system_font", [](const std::string& family, int weight, bool italic) -> nb::object {
        std::string p = FontManager::instance().find_system_font(family, weight, italic);
        if (p.empty()) {
            return nb::none();
        }
        return nb::str(p.c_str());
    }, nb::arg("family"), nb::arg("weight") = 400, nb::arg("italic") = false);

    m.def("get_loaded_fonts", []() {
        return FontManager::instance().get_loaded_fonts();
    });

    m.def("get_internal_fonts", []() {
        return FontManager::instance().get_loaded_fonts();
    });

    m.def("get_system_fonts", [](bool refresh) {
        return FontManager::instance().get_system_fonts(refresh);
    }, nb::arg("refresh") = false);

    m.def("get_active_font", []() -> std::string {
        return FontManager::instance().get_active_font();
    });

    m.def("set_active_font", [](const std::string& family_or_path) -> bool {
        return FontManager::instance().set_active_font(family_or_path);
    }, nb::arg("family_or_path"));

    m.def("register_font_directory", [](const std::string& dir_path) {
        return FontManager::instance().register_font_directory(dir_path);
    }, nb::arg("dir_path"));

    m.def("load_font_face_from_bytes", [](const std::string& name, nb::bytes data) -> bool {
        return FontManager::instance().load_font_face_from_data(name, data.data(), data.size());
    }, nb::arg("name"), nb::arg("data"));

    m.def("ensure_embedded_fonts", []() {
        FontManager::instance().ensure_embedded_fonts_loaded();
    });

    m.def("font_has_glyph", [](const std::string& family, uint32_t codepoint, float size, int weight, bool italic) -> bool {
        BLFont f = FontManager::instance().create_font(family, size, weight, italic);
        return FontManager::font_has_glyph(f, codepoint);
    }, nb::arg("family"), nb::arg("codepoint"), nb::arg("size") = 12.0f, nb::arg("weight") = 400, nb::arg("italic") = false);

    m.def("set_emoji_font", [](const std::string& path) {
        EmojiEngine::instance().set_emoji_font(path);
    }, nb::arg("path"));

    m.def("get_emoji_font", []() -> std::string {
        return EmojiEngine::instance().get_emoji_font_path();
    });

    m.def("clear_font_cache", []() {
        FontManager::instance().clear_cache();
    });

    m.def("clear_shadow_cache", []() {
        ShadowEngine::instance().clear_cache();
    });

    m.def("clear_emoji_cache", []() {
        EmojiEngine::instance().clear_cache();
    });

    m.def("get_shadow_cache_size", []() -> size_t {
        return ShadowEngine::instance().get_cache_size();
    });

    m.def("get_shadow_cache_bytes", []() -> size_t {
        return ShadowEngine::instance().get_cache_bytes();
    });

    m.def("set_shadow_cache_limits", [](size_t max_entries, size_t max_bytes) {
        ShadowEngine::instance().set_cache_limits(max_entries, max_bytes);
    }, nb::arg("max_entries"), nb::arg("max_bytes"));

    m.def("clear_all_caches", []() {
        ShadowEngine::instance().clear_cache();
        FontManager::instance().clear_cache();
        EmojiEngine::instance().clear_cache();
    });
}

// SurfaceBufferObject provides a direct Python buffer protocol view into Surface PRGB32 pixels.
// Full cyclic GC support (Py_TPFLAGS_HAVE_GC, tp_traverse, tp_clear) is implemented so that
// reference cycles between Surface and its active memoryviews can be detected and collected.
struct SurfaceBufferObject {
    PyObject_HEAD
    Surface* surface;
    PyObject* surface_py;
    uint8_t* data;
    size_t size;
    Py_ssize_t shape[1];
    Py_ssize_t strides[1];
};

static PyBufferProcs surface_buffer_as_buffer = {
    [](PyObject* self, Py_buffer* view, int flags) -> int {
        (void)flags;
        auto* obj = reinterpret_cast<SurfaceBufferObject*>(self);
        if (!obj->surface) return -1;
        view->buf = obj->data;
        view->obj = self;
        Py_INCREF(self);
        view->len = static_cast<Py_ssize_t>(obj->size);
        view->readonly = 0;
        view->itemsize = 1;
        view->format = const_cast<char*>("B");
        view->ndim = 1;
        view->shape = obj->shape;
        view->strides = obj->strides;
        view->suboffsets = nullptr;
        view->internal = nullptr;
        return 0;
    },
    [](PyObject*, Py_buffer*) {}
};

static int surface_buffer_traverse(PyObject* self, visitproc visit, void* arg) {
    auto* obj = reinterpret_cast<SurfaceBufferObject*>(self);
    Py_VISIT(obj->surface_py);
    return 0;
}

static int surface_buffer_clear(PyObject* self) {
    auto* obj = reinterpret_cast<SurfaceBufferObject*>(self);
    if (obj->surface) {
        obj->surface->release_buffer_view();
        obj->surface = nullptr;
    }
    Py_CLEAR(obj->surface_py);
    return 0;
}

static void surface_buffer_dealloc(PyObject* self) {
    PyObject_GC_UnTrack(self);
    surface_buffer_clear(self);
    Py_TYPE(self)->tp_free(self);
}

static PyTypeObject SurfaceBufferType = {
    PyVarObject_HEAD_INIT(NULL, 0)
};

static void init_surface_buffer_type() {
    static std::once_flag flag;
    std::call_once(flag, []() {
        SurfaceBufferType.tp_name = "tkblend.SurfaceBuffer";
        SurfaceBufferType.tp_basicsize = sizeof(SurfaceBufferObject);
        SurfaceBufferType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC;
        SurfaceBufferType.tp_doc = "tkblend raw surface buffer wrapper with cyclic GC support";
        SurfaceBufferType.tp_as_buffer = &surface_buffer_as_buffer;
        SurfaceBufferType.tp_traverse = surface_buffer_traverse;
        SurfaceBufferType.tp_clear = surface_buffer_clear;
        SurfaceBufferType.tp_dealloc = surface_buffer_dealloc;
        if (PyType_Ready(&SurfaceBufferType) < 0) {
            throw std::runtime_error("Failed to initialize SurfaceBufferType");
        }
    });
}

void bind_surface(nb::module_& m) {
    init_surface_buffer_type();
    nb::class_<Surface>(m, "Surface")
        .def(nb::init<int, int>(), nb::arg("width"), nb::arg("height"))
        .def("close", &Surface::close)
        .def_prop_ro("is_closed", &Surface::is_closed)
        .def_prop_ro("width", &Surface::width)
        .def_prop_ro("height", &Surface::height)
        .def("resize", &Surface::resize, nb::arg("width"), nb::arg("height"), nb::call_guard<nb::gil_scoped_release>())
        .def("clear", &Surface::clear, nb::arg("color"))
        .def("clear_rect", &Surface::clear_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("save", &Surface::save)
        .def("restore", &Surface::restore)
        .def("reset_transform", &Surface::reset_transform)
        .def("translate", &Surface::translate, nb::arg("tx"), nb::arg("ty"))
        .def("scale", &Surface::scale, nb::arg("sx"), nb::arg("sy"))
        .def("rotate", &Surface::rotate, nb::arg("angle_rad"))
        .def("clip_rect", &Surface::clip_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("clip_rounded_rect", &Surface::clip_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"))
        .def("reset_clip", &Surface::reset_clip)
        .def("set_comp_op", &Surface::set_comp_op, nb::arg("comp_op"))
        .def("set_global_alpha", &Surface::set_global_alpha, nb::arg("alpha"))
        
        // Rectangles & Rounded Rectangles
        .def("fill_rect", &Surface::fill_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"))
        .def("fill_rect_gradient", &Surface::fill_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("gradient"))
        .def("stroke_rect", &Surface::stroke_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_rounded_rect", &Surface::fill_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("fill_rounded_rect_gradient", &Surface::fill_rounded_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("gradient"))
        .def("stroke_rounded_rect", &Surface::stroke_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Circles & Ellipses
        .def("fill_circle", &Surface::fill_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"))
        .def("fill_circle_gradient", &Surface::fill_circle_gradient, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("gradient"))
        .def("stroke_circle", &Surface::stroke_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_ellipse", &Surface::fill_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("stroke_ellipse", &Surface::stroke_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Lines & Paths
        .def("draw_line", &Surface::draw_line, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_path", &Surface::fill_path, nb::arg("path"), nb::arg("color"))
        .def("fill_path_gradient", &Surface::fill_path_gradient, nb::arg("path"), nb::arg("gradient"))
        .def("stroke_path", &Surface::stroke_path, nb::arg("path"), nb::arg("color"), nb::arg("stroke_width") = 1.0)

        // Typography & Metrics
        .def("measure_text", [](Surface& s,
                                const std::string& text, float font_size,
                                const std::string& font_family, int weight,
                                bool italic, bool bold) {
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            return s.measure_text(text, font_size, font_family, eff_weight, italic);
        },
             nb::arg("text"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false)

        .def("break_lines", [](Surface& s,
                               const std::string& text, double max_width,
                               float font_size, const std::string& font_family,
                               int weight, bool italic, bool bold,
                               bool truncate_ellipsis, int max_lines) {
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            return s.break_lines(text, max_width, font_size, font_family, eff_weight, italic, truncate_ellipsis, max_lines);
        },
             nb::arg("text"), nb::arg("max_width"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("truncate_ellipsis") = false,
             nb::arg("max_lines") = 0)

        .def("draw_text", [](Surface& s,
                             const std::string& text, double x, double y,
                             float font_size, const std::string& font_family,
                             std::optional<Color> color, int align,
                             int weight, bool italic, bool bold) {
            Color col = color.value_or(Color(255, 255, 255, 255));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) {
                eff_weight = 700;
            }
            s.draw_text(text, x, y, font_size, font_family, col, align, eff_weight, italic);
        },
             nb::arg("text"), nb::arg("x"), nb::arg("y"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("color") = nb::none(),
             nb::arg("align") = 0,
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false)

        .def("draw_text_wrapped", [](Surface& s,
                                     const std::string& text, double x, double y,
                                     double max_width, float font_size,
                                     const std::string& font_family,
                                     std::optional<Color> color, int align,
                                     int weight, bool italic, bool bold,
                                     double line_height_factor, bool truncate_ellipsis,
                                     int max_lines) {
            Color col = color.value_or(Color(255, 255, 255, 255));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            s.draw_text_wrapped(text, x, y, max_width, font_size, font_family, col, align, eff_weight, italic, line_height_factor, truncate_ellipsis, max_lines);
        },
             nb::arg("text"), nb::arg("x"), nb::arg("y"), nb::arg("max_width"),
             nb::arg("font_size") = 14.0f,
             nb::arg("font_family") = "default",
             nb::arg("color") = nb::none(),
             nb::arg("align") = 0,
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("line_height_factor") = 1.25,
             nb::arg("truncate_ellipsis") = false,
             nb::arg("max_lines") = 0)

        .def("draw_icon", [](Surface& s,
                             const std::string& icon_char_or_name,
                             double x, double y,
                             float size,
                             const std::string& font_family,
                             std::optional<Color> color,
                             int align) {
            Color col = color.value_or(Color(255, 255, 255, 255));
            s.draw_icon(icon_char_or_name, x, y, size, col, font_family, align);
        },
             nb::arg("icon"), nb::arg("x"), nb::arg("y"),
             nb::arg("size") = 16.0f,
             nb::arg("font_family") = "fa-solid",
             nb::arg("color") = nb::none(),
             nb::arg("align") = 0)

        // Shadows & Cards
        .def("render_box", [](Surface& s,
                              double x, double y, double w, double h,
                              const ComputedStyle& style,
                              const std::string& text,
                              int text_align) {
            s.render_box(x, y, w, h, style, text, text_align);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("style"), nb::arg("text") = "", nb::arg("text_align") = 1,
             nb::call_guard<nb::gil_scoped_release>())

        .def("render_styled_box", [](Surface& s,
                                     const std::string& element,
                                     const std::string& class_name,
                                     uint16_t state,
                                     double scale,
                                     const Color& parent_bg,
                                     const std::string& text,
                                     int text_align,
                                     std::optional<double> custom_rx,
                                     std::optional<double> custom_ry,
                                     double elevation,
                                     std::optional<Color> explicit_bg,
                                     std::optional<Color> explicit_fg,
                                     std::optional<Color> explicit_border,
                                     const std::string& font_family,
                                     float font_size,
                                     int font_weight) {
            s.render_styled_box(
                element, class_name, state, scale, parent_bg, text, text_align,
                custom_rx, custom_ry, elevation,
                explicit_bg, explicit_fg, explicit_border,
                font_family, font_size, font_weight
            );
        },
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("text_align") = 1,
             nb::arg("custom_rx") = nb::none(),
             nb::arg("custom_ry") = nb::none(),
             nb::arg("elevation") = 0.0,
             nb::arg("explicit_bg") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("explicit_border") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_shadow_rounded_rect", [](Surface& s,
                                            double x, double y, double w, double h,
                                            double rx, double ry,
                                            double blur_radius, double spread,
                                            double offset_x, double offset_y,
                                            std::optional<Color> shadow_color) {
            Color sc = shadow_color.value_or(Color(0, 0, 0, 128));
            s.draw_shadow_rounded_rect(x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("blur_radius"), nb::arg("spread") = 0.0,
             nb::arg("offset_x") = 0.0, nb::arg("offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_card", [](Surface& s,
                             double x, double y, double w, double h,
                             double rx, double ry,
                             const Color& bg_color,
                             std::optional<Color> border_color,
                             double border_width,
                             double shadow_blur,
                             double shadow_spread,
                             double shadow_offset_x,
                             double shadow_offset_y,
                             std::optional<Color> shadow_color) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color sc = shadow_color.value_or(Color(0, 0, 0, 0));
            s.draw_card(x, y, w, h, rx, ry, bg_color, bc, border_width,
                        shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, sc);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_spread") = 0.0,
             nb::arg("shadow_offset_x") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())

        // Compound Widgets
        .def("draw_button", [](Surface& s,
                               double x, double y, double w, double h,
                               double rx, double ry,
                               const Color& bg_color,
                               std::optional<Color> border_color,
                               double border_width,
                               std::optional<Color> fg_color,
                               const std::string& text,
                               float font_size,
                               const std::string& font_family,
                               int weight,
                               bool italic,
                               bool bold,
                               double shadow_blur,
                               double shadow_offset_y,
                               std::optional<Color> shadow_color,
                               std::optional<Color> focus_ring_color,
                               double focus_ring_width,
                               bool is_pressed) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color fgc = fg_color.value_or(Color(255, 255, 255, 255));
            Color sc = shadow_color.value_or(Color(0, 0, 0, 0));
            Color frc = focus_ring_color.value_or(Color(0, 0, 0, 0));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            s.draw_button(x, y, w, h, rx, ry, bg_color, bc, border_width, fgc,
                          text, font_size, font_family, eff_weight, italic,
                          shadow_blur, shadow_offset_y, sc, frc, focus_ring_width, is_pressed);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("bg_color"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("fg_color") = nb::none(),
             nb::arg("text") = "",
             nb::arg("font_size") = 13.0f,
             nb::arg("font_family") = "default",
             nb::arg("weight") = 400,
             nb::arg("italic") = false,
             nb::arg("bold") = false,
             nb::arg("shadow_blur") = 0.0,
             nb::arg("shadow_offset_y") = 0.0,
             nb::arg("shadow_color") = nb::none(),
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::arg("is_pressed") = false,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_switch", [](Surface& s,
                              double x, double y, double w, double h,
                              const Color& track_color,
                              const Color& thumb_color,
                              std::optional<Color> thumb_border_color,
                              double progress_t,
                              bool is_hovered,
                              std::optional<Color> focus_ring_color,
                              double focus_ring_width) {
            Color tbc = thumb_border_color.value_or(Color(0, 0, 0, 0));
            Color frc = focus_ring_color.value_or(Color(0, 0, 0, 0));
            s.draw_switch(x, y, w, h, track_color, thumb_color, tbc, progress_t, is_hovered, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("track_color"),
             nb::arg("thumb_color"),
             nb::arg("thumb_border_color") = nb::none(),
             nb::arg("progress_t") = 0.0,
             nb::arg("is_hovered") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_slider", [](Surface& s,
                              double x, double y, double w, double h,
                              const Color& track_bg,
                              const Color& active_bg,
                              const Color& thumb_color,
                              std::optional<Color> thumb_border_color,
                              double value_t,
                              double track_thickness,
                              double thumb_radius,
                              bool is_hovered,
                              bool is_dragging,
                              std::optional<Color> focus_ring_color,
                              double focus_ring_width) {
            Color tbc = thumb_border_color.value_or(Color(0, 0, 0, 0));
            Color frc = focus_ring_color.value_or(Color(0, 0, 0, 0));
            s.draw_slider(x, y, w, h, track_bg, active_bg, thumb_color, tbc,
                          value_t, track_thickness, thumb_radius, is_hovered, is_dragging, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("track_bg"),
             nb::arg("active_bg"),
             nb::arg("thumb_color"),
             nb::arg("thumb_border_color") = nb::none(),
             nb::arg("value_t") = 0.0,
             nb::arg("track_thickness") = 4.0,
             nb::arg("thumb_radius") = 8.0,
             nb::arg("is_hovered") = false,
             nb::arg("is_dragging") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_progress_bar", &Surface::draw_progress_bar,
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("track_bg"),
             nb::arg("bar_bg"),
             nb::arg("progress_t") = 0.0,
             nb::arg("is_indeterminate") = false,
             nb::arg("phase_offset") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        .def("draw_checkbox", [](Surface& s,
                                double x, double y, double size,
                                double rx, double ry,
                                const Color& box_bg,
                                std::optional<Color> border_color,
                                double border_width,
                                std::optional<Color> check_color,
                                bool is_checked,
                                bool is_hovered,
                                std::optional<Color> focus_ring_color,
                                double focus_ring_width) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color cc = check_color.value_or(Color(255, 255, 255, 255));
            Color frc = focus_ring_color.value_or(Color(0, 0, 0, 0));
            s.draw_checkbox(x, y, size, rx, ry, box_bg, bc, border_width, cc, is_checked, is_hovered, frc, focus_ring_width);
        },
             nb::arg("x"), nb::arg("y"), nb::arg("size"),
             nb::arg("rx"), nb::arg("ry"),
             nb::arg("box_bg"),
             nb::arg("border_color") = nb::none(),
             nb::arg("border_width") = 0.0,
             nb::arg("check_color") = nb::none(),
             nb::arg("is_checked") = false,
             nb::arg("is_hovered") = false,
             nb::arg("focus_ring_color") = nb::none(),
             nb::arg("focus_ring_width") = 0.0,
             nb::call_guard<nb::gil_scoped_release>())

        // Batch Execution
        .def("execute_batch", &Surface::execute_batch,
             nb::arg("batch"),
             nb::call_guard<nb::gil_scoped_release>())

        // Tkinter Blit & Buffer
        .def("attach_to_widget", &Surface::attach_to_widget,
             nb::arg("interp_addr"), nb::arg("widget_path"))
        .def("detach_widget", &Surface::detach_widget)
        .def("present", &Surface::present)
        .def("flush", &Surface::flush, nb::call_guard<nb::gil_scoped_release>())
        .def("blit_to_photo", &Surface::blit_to_photo,
             nb::arg("interp_addr"), nb::arg("photo_name"),
             nb::arg("dst_x") = 0, nb::arg("dst_y") = 0)
        .def("stride", &Surface::stride)
        .def("size_in_bytes", &Surface::size_in_bytes)
        .def("active_buffers", &Surface::active_buffers)
        
        .def("get_buffer", [](nb::handle self) -> nb::object {
            Surface& s = nb::cast<Surface&>(self);
            if (s.is_closed()) {
                throw std::runtime_error("Cannot get buffer from a closed Surface");
            }
            init_surface_buffer_type();
            auto* obj = PyObject_GC_New(SurfaceBufferObject, &SurfaceBufferType);
            if (!obj) {
                throw std::runtime_error("Failed to allocate SurfaceBufferObject");
            }
            obj->surface = &s;
            obj->surface_py = self.ptr();
            Py_INCREF(self.ptr());

            auto info = s.acquire_buffer_view();
            obj->data = info.data;
            obj->size = info.size;
            obj->shape[0] = static_cast<Py_ssize_t>(info.size);
            obj->strides[0] = 1;

            PyObject_GC_Track(reinterpret_cast<PyObject*>(obj));

            PyObject* mem = PyMemoryView_FromObject(reinterpret_cast<PyObject*>(obj));
            Py_DECREF(reinterpret_cast<PyObject*>(obj));
            if (!mem) {
                throw std::runtime_error("Failed to create memoryview from surface buffer");
            }
            return nb::steal(mem);
        });
}

void bind_window_shape(nb::module_& m) {
    m.def("is_window_shaping_supported", &is_window_shaping_supported,
          "Check if hardware/OS window shaping is supported on current platform.");
    m.def("apply_round_rect_shape", &apply_round_rect_shape,
          nb::arg("window_id"), nb::arg("width"), nb::arg("height"), nb::arg("rx"), nb::arg("ry"),
          "Clip native window region to a rounded rectangle.");
    m.def("clear_window_shape", &clear_window_shape,
          nb::arg("window_id"),
          "Reset native window region to default rectangle.");
}

void bind_style_engine(nb::module_& m) {
    nb::enum_<PseudoState>(m, "PseudoState", nb::is_arithmetic())
        .value("Normal", PseudoState::Normal)
        .value("Hover", PseudoState::Hover)
        .value("Active", PseudoState::Active)
        .value("Focused", PseudoState::Focused)
        .value("Disabled", PseudoState::Disabled)
        .value("Checked", PseudoState::Checked)
        .export_values();

    nb::class_<ComputedStyle>(m, "ComputedStyle")
        .def(nb::init<>())
        .def_rw("bg_color", &ComputedStyle::bg_color)
        .def_rw("fg_color", &ComputedStyle::fg_color)
        .def_rw("border_color", &ComputedStyle::border_color)
        .def_rw("border_width", &ComputedStyle::border_width)
        .def_rw("border_radius", &ComputedStyle::border_radius)
        .def_rw("shadow_blur", &ComputedStyle::shadow_blur)
        .def_rw("shadow_offset_x", &ComputedStyle::shadow_offset_x)
        .def_rw("shadow_offset_y", &ComputedStyle::shadow_offset_y)
        .def_rw("shadow_color", &ComputedStyle::shadow_color)
        .def_rw("font_size", &ComputedStyle::font_size)
        .def_rw("font_weight", &ComputedStyle::font_weight)
        .def_rw("font_family", &ComputedStyle::font_family)
        .def("__repr__", [](const ComputedStyle& cs) {
            std::ostringstream ss;
            ss << "ComputedStyle(bg_color=" << cs.bg_color.to_u32()
               << ", border_radius=" << cs.border_radius
               << ", border_width=" << cs.border_width
               << ", shadow_blur=" << cs.shadow_blur
               << ", font_size=" << cs.font_size << ")";
            return ss.str();
        });

    nb::class_<StyleEngine>(m, "StyleEngine")
        .def_static("get", &StyleEngine::instance, nb::rv_policy::reference)
        .def_static("load_stylesheet", [](const std::string& css) {
            StyleEngine::instance().load_stylesheet(css);
        }, nb::arg("css_text"))
        .def_static("set_theme", [](const std::string& theme_name) {
            StyleEngine::instance().set_theme(theme_name);
        }, nb::arg("theme_name"))
        .def_static("get_theme", []() {
            return StyleEngine::instance().get_theme();
        })
        .def_static("get_available_themes", []() {
            return StyleEngine::instance().get_available_themes();
        })
        .def_static("register_theme", [](const std::string& theme, const std::string& css) {
            StyleEngine::instance().register_theme(theme, css);
        }, nb::arg("theme_name"), nb::arg("css_text"))
        .def_static("resolve", [](const std::string& element, const std::string& class_name, uint16_t states) {
            return StyleEngine::instance().resolve(element, class_name, states);
        }, nb::arg("element") = "", nb::arg("class_name") = "", nb::arg("states") = 0)
        .def_static("resolve_color", [](const std::string& color_str) {
            return StyleEngine::instance().resolve_color(color_str);
        }, nb::arg("color_str"))
        .def_static("set_variable", [](const std::string& key, const std::string& val, const std::string& theme_name) {
            StyleEngine::instance().set_variable(key, val, theme_name);
        }, nb::arg("key"), nb::arg("val"), nb::arg("theme_name") = "")
        .def_static("get_variable", [](const std::string& key, const std::string& theme_name) {
            return StyleEngine::instance().get_variable(key, theme_name);
        }, nb::arg("key"), nb::arg("theme_name") = "")
        .def_static("clear_cache", []() {
            StyleEngine::instance().clear_cache();
        });
}

void bind_surface_handle(nb::module_& m) {
    nb::class_<SurfaceHandle>(m, "SurfaceHandle")
        .def(nb::init<int, int>(), nb::arg("width") = 1, nb::arg("height") = 1)
        .def_prop_ro("surface_id", &SurfaceHandle::surface_id)
        .def_prop_ro("width", &SurfaceHandle::width)
        .def_prop_ro("height", &SurfaceHandle::height)
        .def_prop_ro("is_closed", &SurfaceHandle::is_closed)
        .def("resize", &SurfaceHandle::resize, nb::arg("width"), nb::arg("height"), nb::call_guard<nb::gil_scoped_release>())
        .def("clear", &SurfaceHandle::clear, nb::arg("color"), nb::call_guard<nb::gil_scoped_release>())
        .def("clear_rect", &SurfaceHandle::clear_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::call_guard<nb::gil_scoped_release>())
        .def("render_box", &SurfaceHandle::render_box,
             nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"),
             nb::arg("style"), nb::arg("text") = "", nb::arg("text_align") = 1,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_box", &SurfaceHandle::render_styled_box,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("text_align") = 1,
             nb::arg("custom_rx") = nb::none(),
             nb::arg("custom_ry") = nb::none(),
             nb::arg("elevation") = 0.0,
             nb::arg("explicit_bg") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("explicit_border") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_badge", &SurfaceHandle::render_styled_badge,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("dot") = false,
             nb::arg("dot_color") = nb::none(),
             nb::arg("custom_rx") = nb::none(),
             nb::arg("custom_ry") = nb::none(),
             nb::arg("explicit_bg") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("explicit_border") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_checkbox", &SurfaceHandle::render_styled_checkbox,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("is_checked") = false,
             nb::arg("box_size") = 18.0,
             nb::arg("custom_rx") = nb::none(),
             nb::arg("custom_ry") = nb::none(),
             nb::arg("explicit_box_bg") = nb::none(),
             nb::arg("explicit_border") = nb::none(),
             nb::arg("explicit_check_color") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_radio", &SurfaceHandle::render_styled_radio,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("is_selected") = false,
             nb::arg("circle_size") = 18.0,
             nb::arg("explicit_bg") = nb::none(),
             nb::arg("explicit_border") = nb::none(),
             nb::arg("explicit_dot_color") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_switch", &SurfaceHandle::render_styled_switch,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("text") = "",
             nb::arg("progress_t") = 0.0,
             nb::arg("switch_w") = 44.0,
             nb::arg("switch_h") = 24.0,
             nb::arg("explicit_track_on") = nb::none(),
             nb::arg("explicit_track_off") = nb::none(),
             nb::arg("explicit_thumb") = nb::none(),
             nb::arg("explicit_fg") = nb::none(),
             nb::arg("font_family") = "",
             nb::arg("font_size") = 0.0f,
             nb::arg("font_weight") = 0,
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_slider", &SurfaceHandle::render_styled_slider,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("value_t") = 0.0,
             nb::arg("track_thickness") = 4.0,
             nb::arg("thumb_radius") = 8.0,
             nb::arg("is_dragging") = false,
             nb::arg("explicit_track_bg") = nb::none(),
             nb::arg("explicit_active_bg") = nb::none(),
             nb::arg("explicit_thumb_color") = nb::none(),
             nb::arg("explicit_border_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_progress", &SurfaceHandle::render_styled_progress,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("state"), nb::arg("scale"),
             nb::arg("parent_bg"), nb::arg("progress_t") = 0.0,
             nb::arg("is_indeterminate") = false,
             nb::arg("phase_offset") = 0.0,
             nb::arg("custom_rx") = nb::none(),
             nb::arg("custom_ry") = nb::none(),
             nb::arg("explicit_track_bg") = nb::none(),
             nb::arg("explicit_fill_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())
        .def("render_styled_separator", &SurfaceHandle::render_styled_separator,
             nb::arg("element"), nb::arg("class_name"),
             nb::arg("scale"), nb::arg("parent_bg"),
             nb::arg("orientation") = "horizontal",
             nb::arg("thickness") = 1.0,
             nb::arg("explicit_color") = nb::none(),
             nb::call_guard<nb::gil_scoped_release>())
        .def("attach_to_widget", &SurfaceHandle::attach_to_widget,
             nb::arg("interp_addr"), nb::arg("widget_path"))
        .def("detach_widget", &SurfaceHandle::detach_widget)
        .def("present", &SurfaceHandle::present)
        .def("blit_to_photo", &SurfaceHandle::blit_to_photo,
             nb::arg("interp_addr"), nb::arg("photo_name"), nb::arg("dst_x") = 0, nb::arg("dst_y") = 0)
        .def("close", &SurfaceHandle::close)
        .def("flush", &SurfaceHandle::flush, nb::call_guard<nb::gil_scoped_release>())
        .def("stride", &SurfaceHandle::stride)
        .def("size_in_bytes", &SurfaceHandle::size_in_bytes)
        .def("active_buffers", &SurfaceHandle::active_buffers)
        .def("get_buffer", [](nb::handle self) -> nb::object {
            SurfaceHandle& h = nb::cast<SurfaceHandle&>(self);
            if (h.is_closed()) {
                throw std::runtime_error("Cannot get buffer from a closed SurfaceHandle");
            }
            Surface& s = h.surface();
            init_surface_buffer_type();
            auto* obj = PyObject_GC_New(SurfaceBufferObject, &SurfaceBufferType);
            if (!obj) {
                throw std::runtime_error("Failed to allocate SurfaceBufferObject");
            }
            obj->surface = &s;
            obj->surface_py = self.ptr();
            Py_INCREF(self.ptr());

            auto info = h.acquire_buffer_view();
            obj->data = info.data;
            obj->size = info.size;
            obj->shape[0] = static_cast<Py_ssize_t>(info.size);
            obj->strides[0] = 1;

            PyObject_GC_Track(reinterpret_cast<PyObject*>(obj));

            PyObject* mem = PyMemoryView_FromObject(reinterpret_cast<PyObject*>(obj));
            Py_DECREF(reinterpret_cast<PyObject*>(obj));
            if (!mem) {
                throw std::runtime_error("Failed to create memoryview from surface buffer");
            }
            return nb::steal(mem);
        })
        .def("execute_batch", &SurfaceHandle::execute_batch, nb::arg("batch"), nb::call_guard<nb::gil_scoped_release>())
        .def("save", &SurfaceHandle::save)
        .def("restore", &SurfaceHandle::restore)
        .def("reset_transform", &SurfaceHandle::reset_transform)
        .def("translate", &SurfaceHandle::translate, nb::arg("tx"), nb::arg("ty"))
        .def("scale", &SurfaceHandle::scale, nb::arg("sx"), nb::arg("sy"))
        .def("rotate", &SurfaceHandle::rotate, nb::arg("angle_rad"))
        .def("clip_rect", &SurfaceHandle::clip_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"))
        .def("clip_rounded_rect", &SurfaceHandle::clip_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"))
        .def("reset_clip", &SurfaceHandle::reset_clip)
        .def("set_comp_op", &SurfaceHandle::set_comp_op, nb::arg("comp_op"))
        .def("set_global_alpha", &SurfaceHandle::set_global_alpha, nb::arg("alpha"))
        .def("fill_rect", &SurfaceHandle::fill_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"))
        .def("fill_rect_gradient", &SurfaceHandle::fill_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("gradient"))
        .def("stroke_rect", &SurfaceHandle::stroke_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_rounded_rect", &SurfaceHandle::fill_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("fill_rounded_rect_gradient", &SurfaceHandle::fill_rounded_rect_gradient, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("gradient"))
        .def("stroke_rounded_rect", &SurfaceHandle::stroke_rounded_rect, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_circle", &SurfaceHandle::fill_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"))
        .def("fill_circle_gradient", &SurfaceHandle::fill_circle_gradient, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("gradient"))
        .def("stroke_circle", &SurfaceHandle::stroke_circle, nb::arg("cx"), nb::arg("cy"), nb::arg("r"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_ellipse", &SurfaceHandle::fill_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"))
        .def("stroke_ellipse", &SurfaceHandle::stroke_ellipse, nb::arg("cx"), nb::arg("cy"), nb::arg("rx"), nb::arg("ry"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_line", &SurfaceHandle::draw_line, nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("fill_path", &SurfaceHandle::fill_path, nb::arg("path"), nb::arg("color"))
        .def("fill_path_gradient", &SurfaceHandle::fill_path_gradient, nb::arg("path"), nb::arg("gradient"))
        .def("stroke_path", &SurfaceHandle::stroke_path, nb::arg("path"), nb::arg("color"), nb::arg("stroke_width") = 1.0)
        .def("draw_text", [](SurfaceHandle& h, const std::string& text, double x, double y, float font_size, const std::string& font_family, std::optional<Color> color, int align, int weight, bool italic, bool bold) {
            Color col = color.value_or(Color(255, 255, 255, 255));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            h.draw_text(text, x, y, font_size, font_family, col, align, eff_weight, italic);
        }, nb::arg("text"), nb::arg("x"), nb::arg("y"), nb::arg("font_size") = 14.0f, nb::arg("font_family") = "default", nb::arg("color") = nb::none(), nb::arg("align") = 0, nb::arg("weight") = 400, nb::arg("italic") = false, nb::arg("bold") = false)
        .def("draw_shadow_rounded_rect", [](SurfaceHandle& h, double x, double y, double w, double h_dim, double rx, double ry, double blur_radius, double spread, double offset_x, double offset_y, std::optional<Color> shadow_color) {
            Color sc = shadow_color.value_or(Color(0, 0, 0, 128));
            h.draw_shadow_rounded_rect(x, y, w, h_dim, rx, ry, blur_radius, spread, offset_x, offset_y, sc);
        }, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("blur_radius"), nb::arg("spread") = 0.0, nb::arg("offset_x") = 0.0, nb::arg("offset_y") = 0.0, nb::arg("shadow_color") = nb::none(), nb::call_guard<nb::gil_scoped_release>())
        .def("draw_card", [](SurfaceHandle& h, double x, double y, double w, double h_dim, double rx, double ry, const Color& bg_color, std::optional<Color> border_color, double border_width, double shadow_blur, double shadow_spread, double shadow_offset_x, double shadow_offset_y, std::optional<Color> shadow_color) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color sc = shadow_color.value_or(Color(0, 0, 0, 0));
            h.draw_card(x, y, w, h_dim, rx, ry, bg_color, bc, border_width, shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, sc);
        }, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("bg_color"), nb::arg("border_color") = nb::none(), nb::arg("border_width") = 0.0, nb::arg("shadow_blur") = 0.0, nb::arg("shadow_spread") = 0.0, nb::arg("shadow_offset_x") = 0.0, nb::arg("shadow_offset_y") = 0.0, nb::arg("shadow_color") = nb::none(), nb::call_guard<nb::gil_scoped_release>())
        .def("draw_button", [](SurfaceHandle& h, double x, double y, double w, double h_dim, double rx, double ry, const Color& bg_color, std::optional<Color> border_color, double border_width, std::optional<Color> fg_color, const std::string& text, float font_size, const std::string& font_family, int weight, bool italic, bool bold, double shadow_blur, double shadow_offset_y, std::optional<Color> shadow_color, std::optional<Color> focus_ring_color, double focus_ring_width, bool is_pressed) {
            Color bc = border_color.value_or(Color(0, 0, 0, 0));
            Color fgc = fg_color.value_or(Color(255, 255, 255, 255));
            Color sc = shadow_color.value_or(Color(0, 0, 0, 0));
            Color frc = focus_ring_color.value_or(Color(0, 0, 0, 0));
            int eff_weight = weight;
            if (bold && eff_weight <= 400) eff_weight = 700;
            h.draw_button(x, y, w, h_dim, rx, ry, bg_color, bc, border_width, fgc, text, font_size, font_family, eff_weight, italic, shadow_blur, shadow_offset_y, sc, frc, focus_ring_width, is_pressed);
        }, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("bg_color"), nb::arg("border_color") = nb::none(), nb::arg("border_width") = 0.0, nb::arg("fg_color") = nb::none(), nb::arg("text") = "", nb::arg("font_size") = 13.0f, nb::arg("font_family") = "default", nb::arg("weight") = 400, nb::arg("italic") = false, nb::arg("bold") = false, nb::arg("shadow_blur") = 0.0, nb::arg("shadow_offset_y") = 0.0, nb::arg("shadow_color") = nb::none(), nb::arg("focus_ring_color") = nb::none(), nb::arg("focus_ring_width") = 0.0, nb::arg("is_pressed") = false, nb::call_guard<nb::gil_scoped_release>())
        .def("draw_switch", &SurfaceHandle::draw_switch, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("track_color"), nb::arg("thumb_color"), nb::arg("thumb_border_color"), nb::arg("progress_t"), nb::arg("is_hovered") = false, nb::arg("focus_ring_color") = Color(0,0,0,0), nb::arg("focus_ring_width") = 0.0, nb::call_guard<nb::gil_scoped_release>())
        .def("draw_slider", &SurfaceHandle::draw_slider, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("track_bg"), nb::arg("active_bg"), nb::arg("thumb_color"), nb::arg("thumb_border_color"), nb::arg("value_t"), nb::arg("track_thickness") = 4.0, nb::arg("thumb_radius") = 8.0, nb::arg("is_hovered") = false, nb::arg("is_dragging") = false, nb::arg("focus_ring_color") = Color(0,0,0,0), nb::arg("focus_ring_width") = 0.0, nb::call_guard<nb::gil_scoped_release>())
        .def("draw_progress_bar", &SurfaceHandle::draw_progress_bar, nb::arg("x"), nb::arg("y"), nb::arg("w"), nb::arg("h"), nb::arg("rx"), nb::arg("ry"), nb::arg("track_bg"), nb::arg("bar_bg"), nb::arg("progress_t"), nb::arg("is_indeterminate") = false, nb::arg("phase_offset") = 0.0, nb::call_guard<nb::gil_scoped_release>())
        .def("draw_checkbox", &SurfaceHandle::draw_checkbox, nb::arg("x"), nb::arg("y"), nb::arg("size"), nb::arg("rx"), nb::arg("ry"), nb::arg("box_bg"), nb::arg("border_color"), nb::arg("border_width"), nb::arg("check_color"), nb::arg("is_checked"), nb::arg("is_hovered") = false, nb::arg("focus_ring_color") = Color(0,0,0,0), nb::arg("focus_ring_width") = 0.0, nb::call_guard<nb::gil_scoped_release>());
}

void bind_surface_registry(nb::module_& m) {
    nb::class_<SurfaceRegistry>(m, "SurfaceRegistry")
        .def_static("instance", &SurfaceRegistry::instance, nb::rv_policy::reference)
        .def("active_surface_count", &SurfaceRegistry::active_surface_count)
        .def("clear_all", &SurfaceRegistry::clear_all);
}

} // anonymous namespace

} // namespace tkblend

NB_MODULE(_tkblend, m) {
    nb::set_leak_warnings(true);
    m.doc() = "High-performance Blend2D vector engine and Tkinter photo blitter";

    tkblend::bind_constants(m);
    tkblend::bind_color(m);
    tkblend::bind_animation(m);
    tkblend::bind_text_metrics(m);
    tkblend::bind_draw_batch(m);
    tkblend::bind_gradient(m);
    tkblend::bind_path(m);
    tkblend::bind_font_manager(m);
    tkblend::bind_surface(m);
    tkblend::bind_window_shape(m);
    tkblend::bind_style_engine(m);
    tkblend::bind_surface_handle(m);
    tkblend::bind_surface_registry(m);

    m.def("attach_widget", [](uintptr_t interp_addr, const std::string& widget_path) -> tkblend::SurfaceHandle {
        return tkblend::SurfaceHandle(tkblend::SurfaceRegistry::instance().create_surface_for_widget(interp_addr, widget_path));
    }, nb::arg("interp_addr"), nb::arg("widget_path"), "Attach a native Blend2D rendering surface to a Tk widget window");
}


