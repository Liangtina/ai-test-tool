---
id: hello-2643
title: Fix starfield canvas to fill entire viewport
type: bug
priority: 2
created: '2026-04-24T23:01:26Z'
updated: '2026-04-24T23:01:49Z'
---

The #starfield canvas uses position:fixed;inset:0 but is missing width:100%;height:100% CSS, and the JS resize handler uses offsetWidth/offsetHeight instead of window.innerWidth/innerHeight. Fix both so the starfield definitively fills the viewport.

### 2026-04-24T23:01:45Z
Fixed: added width:100%;height:100% to #starfield CSS, changed resize() to use window.innerWidth/innerHeight instead of canvas.offsetWidth/offsetHeight. Z-index layering was already correct (starfield:0, card:1).
