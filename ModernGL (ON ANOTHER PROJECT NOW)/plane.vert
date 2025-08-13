#version 330

in vec3 in_position;
in vec3 in_normal;

uniform mat4 u_proj;
uniform mat4 u_view;
uniform mat4 u_model;

out vec3 frag_pos;
out vec3 frag_normal;

void main() {
    vec4 world_pos = u_model * vec4(in_position, 1.0);
    frag_pos = world_pos.xyz;

    mat3 normal_matrix = mat3(transpose(inverse(u_model)));
    frag_normal = normalize(normal_matrix * in_normal);

    gl_Position = u_proj * u_view * world_pos;
}
