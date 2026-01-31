#include "EntityManager.h"
#include "Entity.h"
#include "World.h"
#include "Renderer.h"

EntityManager::EntityManager() {}
EntityManager::~EntityManager() {}

void EntityManager::update(float dt, World& world) {
    for (auto it = ents.begin(); it != ents.end();) {
        auto& e = *it;
        if (!e->alive) { it = ents.erase(it); continue; }
        e->update(dt, world);
        ++it;
    }
}

void EntityManager::render(const Renderer& renderer) const {
    for (auto& e : ents) e->render(renderer);
}

void EntityManager::addEntity(std::unique_ptr<Entity> e) {
    ents.push_back(std::move(e));
}
