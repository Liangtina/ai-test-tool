#pragma once
#include "Math.h"
#include <string>

class World;
class Renderer;

class Entity {
public:
    Vec3 pos;
    Vec3 vel;
    Vec3 size{0.9f,0.9f,0.9f};
    int health = 10;
    bool alive = true;

    Entity() {}
    virtual ~Entity() {}

    virtual void update(float dt, World& world) = 0;
    virtual void render(const class Renderer& renderer) const = 0;

    virtual void onDamage(int amount) { health -= amount; if (health <= 0) alive = false; }
    virtual std::string typeName() const { return "Entity"; }
};
