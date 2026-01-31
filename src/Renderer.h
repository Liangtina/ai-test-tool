#pragma once
#include "World.h"

class Renderer {
public:
    Renderer();
    ~Renderer();
    bool init();
    void renderWorld(const World& world);

    // Entity rendering helpers
    bool initEntityRenderer();
    void renderEntityCube(const Vec3& pos, const Vec3& size, float r, float g, float b) const;
    void renderEntityModel(const float model[16], float r, float g, float b) const;

private:
    unsigned int shaderProgram = 0;
    unsigned int cubeVAO = 0, cubeVBO = 0;
    bool compileShaders();
};
