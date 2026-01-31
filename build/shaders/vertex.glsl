#version 410 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;

out vec3 vColor;

uniform mat4 uProj;
uniform mat4 uModel;
uniform int uUseColor;
uniform vec3 uColor;

void main() {
    vec4 worldPos = uModel * vec4(aPos, 1.0);
    // very simple transform: scale and offset
    vec3 p = worldPos.xyz;
    p.xz -= vec2(16.0, 16.0); // center
    p.y -= 8.0;
    vec4 pos = vec4(p, 1.0);
    gl_Position = uProj * pos;
    if (uUseColor == 1) vColor = uColor; else vColor = aColor;
}
