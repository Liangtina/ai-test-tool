#include "MeshBuilder.h"
#include <vector>
#include <cstring>

// Greedy meshing adapted for 3D voxel chunks
// We create quads per face direction merged on 2D masks.

static void pushQuad(std::vector<float>& vert, std::vector<unsigned int>& idx,
                     float x0,float y0,float z0, float x1,float y1,float z1,
                     const float normal[3], float r, float g, float b) {
    unsigned int start = vert.size() / 9;
    // quad vertices (CCW)
    vert.insert(vert.end(), {x0,y0,z0, normal[0],normal[1],normal[2], r,g,b});
    vert.insert(vert.end(), {x1,y0,z1, normal[0],normal[1],normal[2], r,g,b});
    vert.insert(vert.end(), {x1,y1,z1, normal[0],normal[1],normal[2], r,g,b});
    vert.insert(vert.end(), {x0,y1,z0, normal[0],normal[1],normal[2], r,g,b});
    idx.push_back(start+0); idx.push_back(start+1); idx.push_back(start+2);
    idx.push_back(start+2); idx.push_back(start+3); idx.push_back(start+0);
}

// greedy 2D rectangle merge on mask w x h; mask contains 0 for empty or material id (>0)
static void greedyMerge2D(const uint8_t* mask, int w, int h, std::vector<std::tuple<int,int,int,int,int>>& outRects) {
    // outRects: x,y,width,height,mat
    std::vector<uint8_t> used(w*h);
    memcpy(used.data(), mask, w*h);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            int idx = x + y*w;
            uint8_t mat = used[idx];
            if (!mat) continue;
            // find width
            int width = 1;
            while (x + width < w && used[x+width + y*w] == mat) width++;
            // find height
            int height = 1;
            bool ok = true;
            while (y + height < h && ok) {
                for (int k = 0; k < width; ++k) {
                    if (used[(x+k) + (y+height)*w] != mat) { ok = false; break; }
                }
                if (ok) height++;
            }
            // mark used
            for (int yy = 0; yy < height; ++yy) for (int xx = 0; xx < width; ++xx) used[(x+xx) + (y+yy)*w] = 0;
            outRects.push_back({x,y,width,height,mat});
        }
    }
}

void buildMeshFromBlocks(const uint8_t* blocks, int sx, int sy, int sz, int chunkX, int chunkZ, Mesh& outMesh) {
    auto inBounds = [&](int x, int y, int z) { return x >= 0 && x < sx && y >= 0 && y < sy && z >= 0 && z < sz; };
    auto at = [&](int x, int y, int z) -> uint8_t {
        if (!inBounds(x,y,z)) return 0;
        return blocks[x + sx * (z + sz * y)];
    };

    std::vector<float>& vert = outMesh.vertices;
    std::vector<unsigned int>& idx = outMesh.indices;

    // For each axis (X, Y, Z) build masks and merge
    // X faces (norm +/- X) - iterate x from 0..sx (planes between voxels)
    std::vector<uint8_t> mask(sy*sz);
    for (int x = 0; x <= sx; ++x) {
        // mask for +X faces where block at x is solid and block at x-1 is empty
        for (int y=0;y<sy;++y) for (int z=0;z<sz;++z) {
            uint8_t a = (x < sx) ? at(x,y,z) : 0;
            uint8_t b = (x-1 >= 0) ? at(x-1,y,z) : 0;
            mask[y + sy * z] = (a != 0 && b == 0) ? a : 0;
        }
        std::vector<std::tuple<int,int,int,int,int>> rects;
        greedyMerge2D(mask.data(), sy, sz, rects);
        for (auto &r : rects) {
            int ox, oy, ow, oh, mat; std::tie(ox,oy,ow,oh,mat) = r;
            // mapping: y (0..sy-1) -> oy.., z -> oy? we used y as width in greedy
            float x0 = float(chunkX * sx + x);
            float x1 = x0;
            float y0 = float(ox);
            float y1 = float(ox + ow);
            float z0 = float(chunkZ * sz + oy);
            float z1 = float(chunkZ * sz + oy + oh);
            const float normal[3] = {1,0,0};
            pushQuad(vert, idx, x0, y0, z0, x1, y1, z1, normal, 0.8f,0.7f,0.5f);
        }
    }

    // Y faces (norm +/- Y)
    mask.assign(sx*sz, 0);
    for (int y = 0; y <= sy; ++y) {
        for (int x=0;x<sx;++x) for (int z=0;z<sz;++z) {
            uint8_t a = (y < sy) ? at(x,y,z) : 0;
            uint8_t b = (y-1 >= 0) ? at(x,y-1,z) : 0;
            mask[x + sx * z] = (a != 0 && b == 0) ? a : 0;
        }
        std::vector<std::tuple<int,int,int,int,int>> rects;
        greedyMerge2D(mask.data(), sx, sz, rects);
        for (auto &r : rects) {
            int ox, oy, ow, oh, mat; std::tie(ox,oy,ow,oh,mat) = r;
            float x0 = float(chunkX * sx + ox);
            float x1 = float(chunkX * sx + ox + ow);
            float y0 = float(y);
            float y1 = y0;
            float z0 = float(chunkZ * sz + oy);
            float z1 = float(chunkZ * sz + oy + oh);
            const float normal[3] = {0,1,0};
            pushQuad(vert, idx, x0, y0, z1, x1, y1, z0, normal, 0.3f,0.8f,0.3f);
        }
    }

    // Z faces (norm +/- Z)
    mask.assign(sx*sy, 0);
    for (int z = 0; z <= sz; ++z) {
        for (int x=0;x<sx;++x) for (int y=0;y<sy;++y) {
            uint8_t a = (z < sz) ? at(x,y,z) : 0;
            uint8_t b = (z-1 >= 0) ? at(x,y,z-1) : 0;
            mask[x + sx * y] = (a != 0 && b == 0) ? a : 0;
        }
        std::vector<std::tuple<int,int,int,int,int>> rects;
        greedyMerge2D(mask.data(), sx, sy, rects);
        for (auto &r : rects) {
            int ox, oy, ow, oh, mat; std::tie(ox,oy,ow,oh,mat) = r;
            float x0 = float(chunkX * sx + ox);
            float x1 = float(chunkX * sx + ox + ow);
            float y0 = float(oy);
            float y1 = float(oy + oh);
            float z0 = float(chunkZ * sz + z);
            float z1 = z0;
            const float normal[3] = {0,0,1};
            pushQuad(vert, idx, x1, y0, z0, x0, y1, z1, normal, 0.8f,0.7f,0.5f);
        }
    }
}
