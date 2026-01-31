#pragma once
#include <vector>
#include <memory>

class World;
class Entity;

class EntityManager {
public:
    EntityManager();
    ~EntityManager();

    void update(float dt, World& world);
    void render(const class Renderer& renderer) const;

    void addEntity(std::unique_ptr<Entity> e);
    size_t size() const { return ents.size(); }

private:
    std::vector<std::unique_ptr<Entity>> ents;
};
