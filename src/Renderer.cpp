#include "Renderer.h"
#include <glad/glad.h>
#include <fstream>
#include <sstream>
#include <iostream>

static std::string readFile(const char* path) {
    std::ifstream in(path);
    if (!in) return "";
    std::stringstream ss; ss << in.rdbuf();
    return ss.str();
}

static unsigned int compileShader(unsigned int type, const std::string& src) {
    unsigned int id = glCreateShader(type);
    const char* cstr = src.c_str();
    glShaderSource(id, 1, &cstr, nullptr);
    glCompileShader(id);
    int success; glGetShaderiv(id, GL_COMPILE_STATUS, &success);
    if (!success) {
        char buf[512]; glGetShaderInfoLog(id, 512, nullptr, buf);
        std::cerr << "Shader compile error: " << buf << "\n";
    }
    return id;
}

Renderer::Renderer() {}
Renderer::~Renderer() { if (shaderProgram) glDeleteProgram(shaderProgram); }

bool Renderer::compileShaders() {
    auto vsrc = readFile("shaders/vertex.glsl");
    auto fsrc = readFile("shaders/fragment.glsl");
    if (vsrc.empty() || fsrc.empty()) return false;
    unsigned int vs = compileShader(GL_VERTEX_SHADER, vsrc);
    unsigned int fs = compileShader(GL_FRAGMENT_SHADER, fsrc);
    shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vs);
    glAttachShader(shaderProgram, fs);
    glLinkProgram(shaderProgram);
    int success; glGetProgramiv(shaderProgram, GL_LINK_STATUS, &success);
    if (!success) {
        char buf[512]; glGetProgramInfoLog(shaderProgram, 512, nullptr, buf);
        std::cerr << "Link error: " << buf << "\n";
        return false;
    }
    glDeleteShader(vs); glDeleteShader(fs);
    return true;
}

bool Renderer::init() {
    if (!compileShaders()) return false;
    return initEntityRenderer();
}

bool Renderer::initEntityRenderer() {
    // create a unit cube (centered at origin, size 1)
    float vertices[] = {
        // positions       normals         colors (ignored)
        -0.5f,-0.5f,-0.5f, 0,0,-1, 0,0,0,
         0.5f,-0.5f,-0.5f, 0,0,-1, 0,0,0,
         0.5f, 0.5f,-0.5f, 0,0,-1, 0,0,0,
         0.5f, 0.5f,-0.5f, 0,0,-1, 0,0,0,
        -0.5f, 0.5f,-0.5f, 0,0,-1, 0,0,0,
        -0.5f,-0.5f,-0.5f, 0,0,-1, 0,0,0,

        -0.5f,-0.5f, 0.5f, 0,0,1, 0,0,0,
         0.5f,-0.5f, 0.5f, 0,0,1, 0,0,0,
         0.5f, 0.5f, 0.5f, 0,0,1, 0,0,0,
         0.5f, 0.5f, 0.5f, 0,0,1, 0,0,0,
        -0.5f, 0.5f, 0.5f, 0,0,1, 0,0,0,
        -0.5f,-0.5f, 0.5f, 0,0,1, 0,0,0,

        -0.5f, 0.5f, 0.5f,-1,0,0, 0,0,0,
        -0.5f, 0.5f,-0.5f,-1,0,0, 0,0,0,
        -0.5f,-0.5f,-0.5f,-1,0,0, 0,0,0,
        -0.5f,-0.5f,-0.5f,-1,0,0, 0,0,0,
        -0.5f,-0.5f, 0.5f,-1,0,0, 0,0,0,
        -0.5f, 0.5f, 0.5f,-1,0,0, 0,0,0,

         0.5f, 0.5f, 0.5f, 1,0,0, 0,0,0,
         0.5f, 0.5f,-0.5f, 1,0,0, 0,0,0,
         0.5f,-0.5f,-0.5f, 1,0,0, 0,0,0,
         0.5f,-0.5f,-0.5f, 1,0,0, 0,0,0,
         0.5f,-0.5f, 0.5f, 1,0,0, 0,0,0,
         0.5f, 0.5f, 0.5f, 1,0,0, 0,0,0,

        -0.5f,-0.5f,-0.5f, 0,-1,0, 0,0,0,
         0.5f,-0.5f,-0.5f, 0,-1,0, 0,0,0,
         0.5f,-0.5f, 0.5f, 0,-1,0, 0,0,0,
         0.5f,-0.5f, 0.5f, 0,-1,0, 0,0,0,
        -0.5f,-0.5f, 0.5f, 0,-1,0, 0,0,0,
        -0.5f,-0.5f,-0.5f, 0,-1,0, 0,0,0,

        -0.5f, 0.5f,-0.5f, 0,1,0, 0,0,0,
         0.5f, 0.5f,-0.5f, 0,1,0, 0,0,0,
         0.5f, 0.5f, 0.5f, 0,1,0, 0,0,0,
         0.5f, 0.5f, 0.5f, 0,1,0, 0,0,0,
        -0.5f, 0.5f, 0.5f, 0,1,0, 0,0,0,
        -0.5f, 0.5f,-0.5f, 0,1,0, 0,0,0
    };

    glGenVertexArrays(1, &cubeVAO);
    glGenBuffers(1, &cubeVBO);
    glBindVertexArray(cubeVAO);
    glBindBuffer(GL_ARRAY_BUFFER, cubeVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    GLsizei stride = sizeof(float)*9;
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,(void*)0);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,(void*)(sizeof(float)*3));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2,3,GL_FLOAT,GL_FALSE,stride,(void*)(sizeof(float)*6));
    glBindVertexArray(0);
    return true;
}

void Renderer::renderWorld(const World& world) {
    glUseProgram(shaderProgram);

    // simple projection/view matrices (hard-coded)
    float proj[16] = {
        1.0f,0,0,0,
        0,1.333333f,0,0,
        0,0,-1, -1,
        0,0,-0.2f,0
    };
    int loc = glGetUniformLocation(shaderProgram, "uProj");
    glUniformMatrix4fv(loc, 1, GL_FALSE, proj);

    // draw chunks
    for (auto& c : world.getChunks()) {
        const Mesh& m = c->getMesh();
        if (m.VAO == 0) continue;
        glBindVertexArray(m.VAO);
        glUniform1i(glGetUniformLocation(shaderProgram, "uUseColor"), 0);
        glDrawElements(GL_TRIANGLES, (GLsizei)m.indices.size(), GL_UNSIGNED_INT, 0);
    }
    glBindVertexArray(0);

    // render entities
    glUseProgram(shaderProgram);
    // reuse projection
    world.getEntityManager().render(*this);
}

void Renderer::renderEntityCube(const Vec3& pos, const Vec3& size, float r, float g, float b) const {
    // build a model matrix using helpers (simple translate * scale)
    float model[16] = {
        size.x,0,0,0,
        0,size.y,0,0,
        0,0,size.z,0,
        pos.x,pos.y,pos.z,1
    };
    renderEntityModel(model, r, g, b);
}

void Renderer::renderEntityModel(const float model[16], float r, float g, float b) const {
    glUseProgram(shaderProgram);
    int locM = glGetUniformLocation(shaderProgram, "uModel");
    glUniformMatrix4fv(locM, 1, GL_FALSE, model);
    glUniform1i(glGetUniformLocation(shaderProgram, "uUseColor"), 1);
    glUniform3f(glGetUniformLocation(shaderProgram, "uColor"), r, g, b);

    glBindVertexArray(cubeVAO);
    glDrawArrays(GL_TRIANGLES, 0, 36);
    glBindVertexArray(0);

    glUniform1i(glGetUniformLocation(shaderProgram, "uUseColor"), 0);
}
