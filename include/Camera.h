#pragma once
#include "Math.h"

class Camera {
public:
    Vec3 pos;
    float yaw = -90.0f, pitch = 0.0f;
    float speed = 6.0f;

    Camera() { pos = Vec3(0.0f, 10.0f, 0.0f); }

    Vec3 forward() const {
        float yawr = yaw * 3.14159265f / 180.0f;
        float pitchr = pitch * 3.14159265f / 180.0f;
        Vec3 f;
        f.x = cosf(pitchr) * cosf(yawr);
        f.y = sinf(pitchr);
        f.z = cosf(pitchr) * sinf(yawr);
        return normalize(f);
    }

    Vec3 right() const {
        Vec3 f = forward();
        return normalize(cross(f, Vec3(0,1,0)));
    }

    void moveForward(float dt) { pos = pos + forward() * (speed * dt); }
    void moveBack(float dt) { pos = pos - forward() * (speed * dt); }
    void moveRight(float dt) { pos = pos + right() * (speed * dt); }
    void moveLeft(float dt) { pos = pos - right() * (speed * dt); }

    void processMouse(float dx, float dy) {
        const float sens = 0.1f;
        yaw += dx * sens;
        pitch -= dy * sens;
        if (pitch > 89.0f) pitch = 89.0f;
        if (pitch < -89.0f) pitch = -89.0f;
    }
};
