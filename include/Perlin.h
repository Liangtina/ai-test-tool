#pragma once

// Minimal Perlin-like noise (value noise) for terrain height
#include <cmath>
#include <cstdint>

static inline float fract(float x) { return x - floorf(x); }

static inline float fade(float t) { return t * t * t * (t * (t * 6 - 15) + 10); }

static inline float lerp(float a, float b, float t) { return a + t * (b - a); }

static inline float hash2(int32_t x, int32_t y) {
    int32_t h = x * 374761393 + y * 668265263; // large primes
    h = (h ^ (h >> 13)) * 1274126177;
    return (h & 0x7fffffff) / 2147483647.0f;
}

float valueNoise2D(float x, float y) {
    int32_t xi = (int32_t)floorf(x);
    int32_t yi = (int32_t)floorf(y);
    float xf = fract(x);
    float yf = fract(y);

    float v00 = hash2(xi, yi);
    float v10 = hash2(xi + 1, yi);
    float v01 = hash2(xi, yi + 1);
    float v11 = hash2(xi + 1, yi + 1);

    float u = fade(xf);
    float v = fade(yf);

    float x1 = lerp(v00, v10, u);
    float x2 = lerp(v01, v11, u);
    return lerp(x1, x2, v);
}
