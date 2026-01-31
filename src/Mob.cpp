#include "Mob.h"
#include "World.h"
#include "Renderer.h"
#include <iostream>
#include <algorithm>

Mob::Mob() {
    std::random_device rd; rng.seed(rd());
}

void Mob::update(float dt, World& world) {
    // simple physics
    vel.y -= 9.8f * dt * 0.5f; // mild gravity
    pos = pos + vel * dt;

    // update animation timer
    animTime += dt;

    // decay recent damage
    recentDamage = std::max(0.0f, recentDamage - dt * 1.0f);

    aiTimer += dt;
    if (aiTimer > 0.1f) { // AI tick ~10Hz
        tickAI(aiTimer, world);
        aiTimer = 0.0f;
    }

    // simple clamp to world bounds
    if (pos.y < 0.0f) { pos.y = 0.0f; vel.y = 0.0f; }
}


void Mob::tickAI(float dt, World& world) {
    // Very lightweight 'learning' adjustments are applied when events happen
    // Behavior: if recentDamage > threshold -> flee
    // else small chance to wander

    float fleeScore = recentDamage + (timesHurt * 0.2f);
    float attackScore = aggression + (successfulAttacks * 0.1f);

    if (fleeScore > fearThreshold) {
        state = State::Fleeing;
        // move randomly away (small impulse)
        std::uniform_real_distribution<float> d(-1.0f,1.0f);
        vel.x += d(rng) * 2.0f;
        vel.z += d(rng) * 2.0f;
    } else {
        // wander
        state = State::Wander;
        std::uniform_real_distribution<float> d(-1.0f,1.0f);
        vel.x += d(rng) * 0.5f;
        vel.z += d(rng) * 0.5f;
    }

    // slowly normalize velocity to speed
    float sp = std::sqrt(vel.x*vel.x + vel.z*vel.z);
    if (sp > 0.001f) {
        vel.x = (vel.x / sp) * speed;
        vel.z = (vel.z / sp) * speed;
    }

    // learning decay: adjust thresholds slowly toward base
    fearThreshold = std::clamp(fearThreshold - 0.01f * dt, 0.1f, 1.5f);
    aggression = std::clamp(aggression - 0.005f * dt, 0.0f, 2.0f);
}

void Mob::onDamage(int amount) {
    Entity::onDamage(amount);
    timesHurt++;
    recentDamage += (float)amount;
    // learning update: increase fear, slightly reduce aggression
    fearThreshold = std::min(2.0f, fearThreshold + 0.15f);
    aggression = std::max(0.0f, aggression - 0.05f);
}

void Mob::onAttackSuccess() {
    successfulAttacks++;
    // increase aggression, lower fear
    aggression = std::min(2.0f, aggression + 0.12f);
    fearThreshold = std::max(0.05f, fearThreshold - 0.05f);
}

void Mob::render(const Renderer& renderer) const {
    // color by state for debug: fleeing = red, wander = green, default = yellow
    float r=0.9f, g=0.8f, b=0.2f;
    if (state == State::Fleeing) { r = 0.9f; g = 0.2f; b = 0.2f; }
    else if (state == State::Wander) { r = 0.3f; g = 0.8f; b = 0.3f; }

    // compute simple animation model matrix: idle bob + walk sway
    float speedXZ = std::sqrt(vel.x*vel.x + vel.z*vel.z);
    float bob = 0.0f;
    float yaw = 0.0f;
    if (speedXZ > 0.1f) {
        // walking
        bob = std::sin(animTime * 10.0f) * 0.08f;
        yaw = std::sin(animTime * 6.0f) * 0.12f; // small sway
    } else {
        // idle breathe
        bob = std::sin(animTime * 2.0f) * 0.03f;
    }

    Mat4 T = translate(pos.x, pos.y + bob + 0.3f, pos.z);
    Mat4 R = rotateY(yaw);
    Mat4 S = scaleMat(size.x, size.y, size.z);
    Mat4 M = mul(T, mul(R, S));

    renderer.renderEntityModel(M.m, r, g, b);
}
