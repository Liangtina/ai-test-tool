#pragma once
#include <vector>
#include <cstdint>

static constexpr int CHUNK_SIZE_X = 16;
static constexpr int CHUNK_SIZE_Y = 64;
static constexpr int CHUNK_SIZE_Z = 16;

struct Mesh {
    std::vector<float> vertices; // x,y,z, nx,ny,nz, r,g,b
    std::vector<unsigned int> indices;
    unsigned int VAO = 0, VBO = 0, EBO = 0;
};

class Chunk {
public:
    Chunk(int cx, int cz);
    ~Chunk();

    void generate();

    // Build mesh on CPU (thread safe) then call uploadGPU from main thread
    void buildCPUMesh();
    void uploadGPU();

    const Mesh& getMesh() const { return mesh; }

    // block access
    uint8_t getBlock(int x, int y, int z) const;
    void setBlock(int x, int y, int z, uint8_t v);

    int getChunkX() const { return cx; }
    int getChunkZ() const { return cz; }

private:
    int cx, cz; // chunk coords
    std::vector<uint8_t> blocks; // size: X*Y*Z
    Mesh mesh;

    inline int idx(int x, int y, int z) const { return x + CHUNK_SIZE_X * (z + CHUNK_SIZE_Z * y); }
    inline bool inBounds(int x, int y, int z) const {
        return x >= 0 && x < CHUNK_SIZE_X && y >= 0 && y < CHUNK_SIZE_Y && z >= 0 && z < CHUNK_SIZE_Z;
    }
};
