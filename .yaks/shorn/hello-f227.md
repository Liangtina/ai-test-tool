---
id: hello-f227
title: Make the starfield background "zoom"
type: feature
priority: 2
created: '2026-04-24T17:24:29Z'
updated: '2026-04-24T17:56:10Z'
---

You know, like Star Wars hyperspace-ish.

### 2026-04-24T17:56:08Z
Replaced CSS twinkle divs with a canvas-based hyperspace zoom. Stars shoot outward from center with acceleration, motion-blur trail (semi-transparent bg fill), and size/opacity scaling with distance. 200 stars, recycled when off-screen. Resize-aware.
