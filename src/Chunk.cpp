#include "Chunk.h"
#include "MeshBuilder.h"
#include "Perlin.h"
#include <glad/glad.h>

Chunk::Chunk(int cx_, int cz_) : cx(cx_), cz(cz_) {
    blocks.resize(CHUNK_SIZE_X * CHUNK_SIZE_Y * CHUNK_SIZE_Z);
}

Chunk::~Chunk() {
    if (mesh.VAO) {
        glDeleteVertexArrays(1, &mesh.VAO);
        glDeleteBuffers(1, &mesh.VBO);
        glDeleteBuffers(1, &mesh.EBO);
    }
}

void Chunk::generate() {
    // simple heightmap
    for (int x = 0; x < CHUNK_SIZE_X; ++x) {
        for (int z = 0; z < CHUNK_SIZE_Z; ++z) {
            float wx = float(cx * CHUNK_SIZE_X + x) * 0.08f;
            float wz = float(cz * CHUNK_SIZE_Z + z) * 0.08f;
            float h = (valueNoise2D(wx, wz) * 8.0f) + 8.0f; // 0..16
            int hi = int(h);
            for (int y = 0; y < CHUNK_SIZE_Y; ++y) {
                int index = idx(x, y, z);
                if (y <= hi) blocks[index] = 1; else blocks[index] = 0;
            }
        }
    }
}

void Chunk::buildCPUMesh() {
    // clear old CPU data
    mesh.vertices.clear(); mesh.indices.clear();
    buildMeshFromBlocks(blocks.data(), CHUNK_SIZE_X, CHUNK_SIZE_Y, CHUNK_SIZE_Z, cx, cz, mesh);
}

void Chunk::uploadGPU() {
    // Release prior GL objects
    if (mesh.VAO) {
        glDeleteVertexArrays(1, &mesh.VAO);
        glDeleteBuffers(1, &mesh.VBO);
        glDeleteBuffers(1, &mesh.EBO);
        mesh.VAO = mesh.VBO = mesh.EBO = 0;
    }

    if (mesh.vertices.empty() || mesh.indices.empty()) return;

    glGenVertexArrays(1, &mesh.VAO);
    glGenBuffers(1, &mesh.VBO);
    glGenBuffers(1, &mesh.EBO);

    glBindVertexArray(mesh.VAO);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.VBO);
    glBufferData(GL_ARRAY_BUFFER, mesh.vertices.size() * sizeof(float), mesh.vertices.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.EBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, mesh.indices.size() * sizeof(unsigned int), mesh.indices.data(), GL_STATIC_DRAW);

    // layout: pos(3), normal(3), color(3)
    GLsizei stride = sizeof(float) * 9;
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, (void*)(sizeof(float) * 3));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, (void*)(sizeof(float) * 6));

    glBindVertexArray(0);
}

uint8_t Chunk::getBlock(int x, int y, int z) const {
    if (!inBounds(x,y,z)) return 0;
    return blocks[idx(x,y,z)];
}

void Chunk::setBlock(int x, int y, int z, uint8_t v) {
    if (!inBounds(x,y,z)) return;
    blocks[idx(x,y,z)] = v;
}
