#pragma once

namespace tkblend {

// Easing curves
enum class EasingType {
    Linear = 0,
    QuadIn, QuadOut, QuadInOut,
    CubicIn, CubicOut, CubicInOut,
    QuartIn, QuartOut, QuartInOut,
    SineIn, SineOut, SineInOut,
    ExpoIn, ExpoOut, ExpoInOut,
    CircIn, CircOut, CircInOut,
    ElasticIn, ElasticOut, ElasticInOut,
    BackIn, BackOut, BackInOut,
    BounceIn, BounceOut, BounceInOut
};

double ease(int easing_type, double t);
double spring(double t, double mass = 1.0, double stiffness = 100.0, double damping = 10.0);

} // namespace tkblend
