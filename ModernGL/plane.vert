#version 330

in vec3 in_position;
in vec3 in_normal;

uniform mat4 u_proj;
uniform mat4 u_view;

out vec3 frag_pos;
out vec3 frag_normal;

void main() {
    vec4 world_pos = vec4(in_position, 1.0);
    frag_pos = in_position;
    frag_normal = normalize(in_normal);
    gl_Position = u_proj * u_view * world_pos;
}
