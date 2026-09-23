#include "animation.hpp"
#include <algorithm>
#include <cmath>

namespace tkblend {

namespace {

constexpr double PI = 3.14159265358979323846;
constexpr double c1 = 1.70158;
constexpr double c2 = c1 * 1.525;
constexpr double c3 = c1 + 1.0;
constexpr double c4 = (2.0 * PI) / 3.0;
constexpr double c5 = (2.0 * PI) / 4.5;

double bounce_out(double n) {
    constexpr double n1 = 7.5625;
    constexpr double d1 = 2.75;
    if (n < 1.0 / d1) {
        return n1 * n * n;
    } else if (n < 2.0 / d1) {
        n -= 1.5 / d1;
        return n1 * n * n + 0.75;
    } else if (n < 2.5 / d1) {
        n -= 2.25 / d1;
        return n1 * n * n + 0.9375;
    } else {
        n -= 2.625 / d1;
        return n1 * n * n + 0.984375;
    }
}

} // anonymous namespace

double ease(int easing_type, double t) {
    double x = std::clamp(t, 0.0, 1.0);
    EasingType et = static_cast<EasingType>(easing_type);

    switch (et) {
        case EasingType::Linear: return x;
        case EasingType::QuadIn: return x * x;
        case EasingType::QuadOut: return 1.0 - (1.0 - x) * (1.0 - x);
        case EasingType::QuadInOut: return x < 0.5 ? 2.0 * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 2.0) / 2.0;
        case EasingType::CubicIn: return x * x * x;
        case EasingType::CubicOut: return 1.0 - std::pow(1.0 - x, 3.0);
        case EasingType::CubicInOut: return x < 0.5 ? 4.0 * x * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 3.0) / 2.0;
        case EasingType::QuartIn: return x * x * x * x;
        case EasingType::QuartOut: return 1.0 - std::pow(1.0 - x, 4.0);
        case EasingType::QuartInOut: return x < 0.5 ? 8.0 * x * x * x * x : 1.0 - std::pow(-2.0 * x + 2.0, 4.0) / 2.0;
        case EasingType::SineIn: return 1.0 - std::cos((x * PI) / 2.0);
        case EasingType::SineOut: return std::sin((x * PI) / 2.0);
        case EasingType::SineInOut: return -(std::cos(PI * x) - 1.0) / 2.0;
        case EasingType::ExpoIn: return x == 0.0 ? 0.0 : std::pow(2.0, 10.0 * x - 10.0);
        case EasingType::ExpoOut: return x == 1.0 ? 1.0 : 1.0 - std::pow(2.0, -10.0 * x);
        case EasingType::ExpoInOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : (x < 0.5 ? std::pow(2.0, 20.0 * x - 10.0) / 2.0 : (2.0 - std::pow(2.0, -20.0 * x + 10.0)) / 2.0));
        case EasingType::CircIn: return 1.0 - std::sqrt(1.0 - std::pow(x, 2.0));
        case EasingType::CircOut: return std::sqrt(1.0 - std::pow(x - 1.0, 2.0));
        case EasingType::CircInOut: return x < 0.5 ? (1.0 - std::sqrt(1.0 - std::pow(2.0 * x, 2.0))) / 2.0 : (std::sqrt(1.0 - std::pow(-2.0 * x + 2.0, 2.0)) + 1.0) / 2.0;
        case EasingType::ElasticIn: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : -std::pow(2.0, 10.0 * x - 10.0) * std::sin((x * 10.0 - 10.75) * c4));
        case EasingType::ElasticOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : std::pow(2.0, -10.0 * x) * std::sin((x * 10.0 - 0.75) * c4) + 1.0);
        case EasingType::ElasticInOut: return x == 0.0 ? 0.0 : (x == 1.0 ? 1.0 : (x < 0.5 ? -(std::pow(2.0, 20.0 * x - 10.0) * std::sin((20.0 * x - 11.125) * c5)) / 2.0 : (std::pow(2.0, -20.0 * x + 10.0) * std::sin((20.0 * x - 11.125) * c5)) / 2.0 + 1.0));
        case EasingType::BackIn: return c3 * x * x * x - c1 * x * x;
        case EasingType::BackOut: return 1.0 + c3 * std::pow(x - 1.0, 3.0) + c1 * std::pow(x - 1.0, 2.0);
        case EasingType::BackInOut: return x < 0.5 ? (std::pow(2.0 * x, 2.0) * ((c2 + 1.0) * 2.0 * x - c2)) / 2.0 : (std::pow(2.0 * x - 2.0, 2.0) * ((c2 + 1.0) * (x * 2.0 - 2.0) + c2) + 2.0) / 2.0;
        case EasingType::BounceIn: return 1.0 - bounce_out(1.0 - x);
        case EasingType::BounceOut: return bounce_out(x);
        case EasingType::BounceInOut: return x < 0.5 ? (1.0 - bounce_out(1.0 - 2.0 * x)) / 2.0 : (1.0 + bounce_out(2.0 * x - 1.0)) / 2.0;
    }
    return x;
}

double spring(double t, double mass, double stiffness, double damping) {
    if (t <= 0.0) return 0.0;
    if (t >= 1.0) return 1.0;
    double m = std::max(0.001, mass);
    double k = std::max(0.001, stiffness);
    double c = std::max(0.0, damping);
    double w0 = std::sqrt(k / m);
    double zeta = c / (2.0 * std::sqrt(k * m));

    if (zeta < 1.0) {
        double wd = w0 * std::sqrt(1.0 - zeta * zeta);
        return 1.0 - std::exp(-zeta * w0 * t) * (std::cos(wd * t) + (zeta / std::sqrt(1.0 - zeta * zeta)) * std::sin(wd * t));
    } else {
        return 1.0 - (1.0 + w0 * t) * std::exp(-w0 * t);
    }
}

} // namespace tkblend
