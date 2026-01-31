#pragma once
#include <cmath>

struct Vec3 {
    float x, y, z;
    Vec3() : x(0), y(0), z(0) {}
    Vec3(float X, float Y, float Z) : x(X), y(Y), z(Z) {}
    Vec3 operator+(const Vec3& o) const { return Vec3(x+o.x, y+o.y, z+o.z); }
    Vec3 operator-(const Vec3& o) const { return Vec3(x-o.x, y-o.y, z-o.z); }
    Vec3 operator*(float s) const { return Vec3(x*s, y*s, z*s); }
    Vec3 operator/(float s) const { return Vec3(x/s, y/s, z/s); }
};

static inline float dot(const Vec3& a, const Vec3& b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 cross(const Vec3& a, const Vec3& b) { return Vec3(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x); }
static inline float length(const Vec3& v) { return std::sqrt(dot(v,v)); }
static inline Vec3 normalize(const Vec3& v) { float l = length(v); return l > 0 ? v / l : Vec3(0,0,0); }
static inline Vec3 floorv(const Vec3& v) { return Vec3(std::floor(v.x), std::floor(v.y), std::floor(v.z)); }

struct Mat4 {
    float m[16];
    Mat4() { for (int i=0;i<16;++i) m[i] = 0.0f; }
    static Mat4 identity() { Mat4 a; for (int i=0;i<4;++i) a.m[i*5] = 1.0f; return a; }
};

static inline Mat4 translate(float x, float y, float z) {
    Mat4 t = Mat4::identity();
    t.m[12] = x; t.m[13] = y; t.m[14] = z;
    return t;
}

static inline Mat4 scaleMat(float sx, float sy, float sz) {
    Mat4 s; for (int i=0;i<16;++i) s.m[i]=0.0f; s.m[0]=sx; s.m[5]=sy; s.m[10]=sz; s.m[15]=1.0f; return s;
}

static inline Mat4 rotateY(float rad) {
    Mat4 r = Mat4::identity();
    float c = cosf(rad), s = sinf(rad);
    r.m[0] = c; r.m[2] = s;
    r.m[8] = -s; r.m[10] = c;
    return r;
}

static inline Mat4 mul(const Mat4& a, const Mat4& b) {
    Mat4 r;
    for (int row=0; row<4; ++row) {
        for (int col=0; col<4; ++col) {
            float sum = 0.0f;
            for (int k=0;k<4;++k) sum += a.m[row + k*4] * b.m[k + col*4];
            r.m[row + col*4] = sum;
        }
    }
    return r;
}
