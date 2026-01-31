#pragma once
#include <vector>
#include <memory>
#include <mutex>
#include <queue>
#include "Chunk.h"
#include "Raycast.h"

#include "EntityManager.h"

class World {
public:
    World();
    ~World();
    void init();
    void generateAll();
    void buildAllMeshes();

    // threaded CPU mesh tasks will queue chunks here for GPU upload on main thread
    void processUploadQueue();

    // block access in world coords
    uint8_t getBlockAtWorld(int bx, int by, int bz) const;
    void setBlockAtWorld(int bx, int by, int bz, uint8_t value);

    // raycast that returns first solid block hit
    bool raycast(const Vec3& origin, const Vec3& dir, float maxDist, RaycastHit& out) const;

    const std::vector<std::unique_ptr<Chunk>>& getChunks() const { return chunks; }

    EntityManager& getEntityManager() { return entities; }
    const EntityManager& getEntityManager() const { return entities; }

private:
    std::vector<std::unique_ptr<Chunk>> chunks;

    mutable std::mutex uploadMutex;
    std::queue<Chunk*> uploadQueue;

    Chunk* findChunk(int cx, int cz) const;

    EntityManager entities;
};
