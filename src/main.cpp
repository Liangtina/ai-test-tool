#include <iostream>
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <chrono>
#include "Renderer.h"
#include "World.h"
#include "Camera.h"

// Simple settings
const unsigned int SCR_WIDTH = 1280;
const unsigned int SCR_HEIGHT = 720;

struct AppState { Camera* cam; World* world; bool firstMouse = true; double lastX = SCR_WIDTH/2.0, lastY = SCR_HEIGHT/2.0; };

static void mouse_callback(GLFWwindow* window, double xpos, double ypos) {
    AppState* s = (AppState*)glfwGetWindowUserPointer(window);
    if (!s) return;
    if (s->firstMouse) { s->lastX = xpos; s->lastY = ypos; s->firstMouse = false; }
    float dx = float(xpos - s->lastX);
    float dy = float(ypos - s->lastY);
    s->lastX = xpos; s->lastY = ypos;
    s->cam->processMouse(dx, dy);
}

static void mouse_button_callback(GLFWwindow* window, int button, int action, int mods) {
    if (action != GLFW_PRESS) return;
    AppState* s = (AppState*)glfwGetWindowUserPointer(window);
    if (!s) return;
    RaycastHit hit;
    if (s->world->raycast(s->cam->pos, s->cam->forward(), 64.0f, hit)) {
        if (button == GLFW_MOUSE_BUTTON_LEFT) {
            s->world->setBlockAtWorld(hit.bx, hit.by, hit.bz, 0);
        } else if (button == GLFW_MOUSE_BUTTON_RIGHT) {
            int px = hit.bx - (int)std::round(hit.normal.x);
            int py = hit.by - (int)std::round(hit.normal.y);
            int pz = hit.bz - (int)std::round(hit.normal.z);
            s->world->setBlockAtWorld(px, py, pz, 1);
        }
    }
}

int main() {
    if (!glfwInit()) {
        std::cerr << "Failed to init GLFW\n";
        return -1;
    }

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    GLFWwindow* window = glfwCreateWindow(SCR_WIDTH, SCR_HEIGHT, "Voxel Sandbox (C++)", nullptr, nullptr);
    if (!window) {
        std::cerr << "Failed to create GLFW window\n";
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "Failed to initialize GLAD\n";
        return -1;
    }

    glEnable(GL_DEPTH_TEST);

    Renderer renderer;
    if (!renderer.init()) {
        std::cerr << "Renderer init failed\n";
        return -1;
    }

    World world;
    world.init();

    Camera cam;
    AppState state{&cam, &world, true, double(SCR_WIDTH)/2.0, double(SCR_HEIGHT)/2.0};
    glfwSetWindowUserPointer(window, &state);
    glfwSetCursorPosCallback(window, mouse_callback);
    glfwSetMouseButtonCallback(window, mouse_button_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);

    auto tprev = std::chrono::high_resolution_clock::now();

    // Main loop
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        auto tnow = std::chrono::high_resolution_clock::now();
        float dt = std::chrono::duration<float>(tnow - tprev).count();
        tprev = tnow;

        // controls
        if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS) cam.moveForward(dt);
        if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS) cam.moveBack(dt);
        if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS) cam.moveRight(dt);
        if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS) cam.moveLeft(dt);
        if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS) cam.pos.y += cam.speed * dt;
        if (glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS) cam.pos.y -= cam.speed * dt;

        // process uploaded meshes from worker threads
        world.processUploadQueue();

        int width, height;
        glfwGetFramebufferSize(window, &width, &height);
        glViewport(0, 0, width, height);

        glClearColor(0.6f, 0.8f, 1.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        renderer.renderWorld(world);

        glfwSwapBuffers(window);
    }

    glfwTerminate();
    return 0;
}
