#pragma once
#include "Entity.h"
#include <random>

class Mob : public Entity {
public:
    enum class State {Idle, Wander, Chasing, Attacking, Fleeing, Dead};
    State state = State::Idle;

    // personality / learned params
    float fearThreshold = 0.5f;     // higher => more likely to flee
    float aggression = 0.5f;        // higher => more likely to attack
    float persistence = 0.6f;       // how long to stick to a goal

    // memory
    int timesHurt = 0;
    int successfulAttacks = 0;
    float recentDamage = 0.0f;

    float speed = 1.5f;
    float animTime = 0.0f; // for animation state

    Mob();
    virtual ~Mob() {}

    void update(float dt, World& world) override;
    void render(const class Renderer& renderer) const override;

    void onDamage(int amount) override;
    void onAttackSuccess();

protected:
    std::mt19937 rng;
    float aiTimer = 0.0f;

    void tickAI(float dt, World& world);
};
