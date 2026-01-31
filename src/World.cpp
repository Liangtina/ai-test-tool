#include "World.h"
#include "Mob.h"
#include <iostream>
#include <thread>
#include <cmath>

World::World() {}
World::~World() {}

Chunk* World::findChunk(int cx, int cz) const {
    for (auto& c : chunks) {
        if (c->getChunkX() == cx && c->getChunkZ() == cz) return c.get();
    }
    return nullptr;
}

void World::init() {
    // Simple 3x3 chunk grid centered at 0
    int radius = 1;
    for (int cz = -radius; cz <= radius; ++cz) {
        for (int cx = -radius; cx <= radius; ++cx) {
            auto c = std::make_unique<Chunk>(cx, cz);
            chunks.push_back(std::move(c));
        }
    }

    // generate and build CPU mesh on background threads, then queue upload to main thread
    for (auto& c : chunks) {
        std::thread([this, ptr = c.get()](){
            ptr->generate();
            ptr->buildCPUMesh();
            std::lock_guard<std::mutex> lk(uploadMutex);
            uploadQueue.push(ptr);
        }).detach();
    }

    std::cout << "Scheduled " << chunks.size() << " chunk generation tasks.\n";

    // spawn some mobs for demo: a few wanderers per chunk
    for (auto& c : chunks) {
        int baseX = c->getChunkX() * CHUNK_SIZE_X;
        int baseZ = c->getChunkZ() * CHUNK_SIZE_Z;
        for (int i = 0; i < 2; ++i) {
            auto m = std::make_unique<Mob>();
            m->pos.x = float(baseX + (i*3) + 2);
            // find ground y
            int gx = baseX + (i*3) + 2;
            int gz = baseZ + 2;
            int gy = CHUNK_SIZE_Y - 1;
            for (; gy >= 0; --gy) if (getBlockAtWorld(gx, gy, gz)) break;
            m->pos.y = float(gy + 1);
            m->pos.z = float(gz);
            entities.addEntity(std::move(m));
        }
    }
}

void World::generateAll() {
    for (auto& c : chunks) c->generate();
}

void World::buildAllMeshes() {
    for (auto& c : chunks) c->buildCPUMesh();
}

void World::processUploadQueue() {
    std::lock_guard<std::mutex> lk(uploadMutex);
    while (!uploadQueue.empty()) {
        Chunk* c = uploadQueue.front(); uploadQueue.pop();
        c->uploadGPU();
    }
}

uint8_t World::getBlockAtWorld(int bx, int by, int bz) const {
    int cx = floor((float)bx / CHUNK_SIZE_X);
    int cz = floor((float)bz / CHUNK_SIZE_Z);
    int lx = bx - cx * CHUNK_SIZE_X;
    int lz = bz - cz * CHUNK_SIZE_Z;
    Chunk* c = findChunk(cx, cz);
    if (!c) return 0;
    if (lx < 0 || lx >= CHUNK_SIZE_X || by < 0 || by >= CHUNK_SIZE_Y || lz < 0 || lz >= CHUNK_SIZE_Z) return 0;
    return c->getBlock(lx, by, lz);
}

void World::setBlockAtWorld(int bx, int by, int bz, uint8_t value) {
    int cx = floor((float)bx / CHUNK_SIZE_X);
    int cz = floor((float)bz / CHUNK_SIZE_Z);
    int lx = bx - cx * CHUNK_SIZE_X;
    int lz = bz - cz * CHUNK_SIZE_Z;
    Chunk* c = findChunk(cx, cz);
    if (!c) return;
    if (lx < 0 || lx >= CHUNK_SIZE_X || by < 0 || by >= CHUNK_SIZE_Y || lz < 0 || lz >= CHUNK_SIZE_Z) return;
    c->setBlock(lx, by, lz, value);
    // rebuild CPU mesh in background
    std::thread([this, c](){ c->buildCPUMesh(); std::lock_guard<std::mutex> lk(uploadMutex); uploadQueue.push(c); }).detach();
    // if at edge, rebuild neighbors too (simple check)
    if (lx == 0 || lx == CHUNK_SIZE_X-1 || lz == 0 || lz == CHUNK_SIZE_Z-1) {
        // neighbors offsets
        for (int dz = -1; dz <= 1; ++dz) for (int dx = -1; dx <= 1; ++dx) {
            Chunk* n = findChunk(c->getChunkX() + dx, c->getChunkZ() + dz);
            if (n && n != c) {
                std::thread([this, n](){ n->buildCPUMesh(); std::lock_guard<std::mutex> lk(uploadMutex); uploadQueue.push(n); }).detach();
            }
        }
    }
}

bool World::raycast(const Vec3& origin, const Vec3& dir, float maxDist, RaycastHit& out) const {
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
        uint8_t b = getBlockAtWorld(x,y,z);
        if (b) {
            out.hit = true; out.bx = x; out.by = y; out.bz = z; out.normal = Vec3(0,0,0); // normal isn't tracked perfectly here
            return true;
        }
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
    return false;
}
