#include "Raycast.h"
#include <cmath>

// This is a stand-alone voxel DDA that returns the first integer voxel cell hit along the ray.
RaycastHit raycastVoxel(const Vec3& origin, const Vec3& dir, float maxDist) {
    RaycastHit out;
    Vec3 rayDir = normalize(dir);
    int x = (int)std::floor(origin.x);
    int y = (int)std::floor(origin.y);
    int z = (int)std::floor(origin.z);

    int stepX = rayDir.x > 0 ? 1 : -1;
    int stepY = rayDir.y > 0 ? 1 : -1;
    int stepZ = rayDir.z > 0 ? 1 : -1;

    auto frac = [](float v) { return v - std::floor(v); };

    float tMaxX = (rayDir.x != 0) ? ((stepX > 0 ? (1 - frac(origin.x)) : frac(origin.x)) / std::abs(rayDir.x)) : INFINITY;
    float tMaxY = (rayDir.y != 0) ? ((stepY > 0 ? (1 - frac(origin.y)) : frac(origin.y)) / std::abs(rayDir.y)) : INFINITY;
    float tMaxZ = (rayDir.z != 0) ? ((stepZ > 0 ? (1 - frac(origin.z)) : frac(origin.z)) / std::abs(rayDir.z)) : INFINITY;

    float tDeltaX = (rayDir.x != 0) ? (1.0f / std::abs(rayDir.x)) : INFINITY;
    float tDeltaY = (rayDir.y != 0) ? (1.0f / std::abs(rayDir.y)) : INFINITY;
    float tDeltaZ = (rayDir.z != 0) ? (1.0f / std::abs(rayDir.z)) : INFINITY;

    float t = 0.0f;
    while (t <= maxDist) {
        // We cannot know which voxel is solid here; this function returns the voxel we reach.
        // Caller should check world occupancy at (x,y,z).
        out.hit = true;
        out.bx = x; out.by = y; out.bz = z;

        if (tMaxX < tMaxY) {
            if (tMaxX < tMaxZ) {
                x += stepX; t = tMaxX; tMaxX += tDeltaX; out.normal = Vec3(-stepX,0,0); }
            else { z += stepZ; t = tMaxZ; tMaxZ += tDeltaZ; out.normal = Vec3(0,0,-stepZ); }
        } else {
            if (tMaxY < tMaxZ) {
                y += stepY; t = tMaxY; tMaxY += tDeltaY; out.normal = Vec3(0,-stepY,0); }
            else { z += stepZ; t = tMaxZ; tMaxZ += tDeltaZ; out.normal = Vec3(0,0,-stepZ); }
        }
    }

    return out;
}
