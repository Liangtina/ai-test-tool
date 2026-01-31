#pragma once
#include "Chunk.h"

void buildMeshFromBlocks(const uint8_t* blocks, int sx, int sy, int sz, int chunkX, int chunkZ, Mesh& outMesh);
