#pragma once
#include "Math.h"
#include <tuple>

struct RaycastHit {
    bool hit = false;
    int bx=0, by=0, bz=0;
    Vec3 normal;
};

RaycastHit raycastVoxel(const Vec3& origin, const Vec3& dir, float maxDist);
