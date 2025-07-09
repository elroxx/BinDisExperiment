#version 330

in vec3 frag_pos;
in vec3 frag_normal;

out vec4 frag_color;

uniform vec3 u_camera_pos;
uniform vec3 u_light_pos;
uniform float u_specular_power;

void main() {
    vec3 normal = normalize(frag_normal);
    vec3 light_dir = normalize(u_light_pos - frag_pos);
    vec3 view_dir = normalize(u_camera_pos - frag_pos);
    vec3 halfway = normalize(light_dir + view_dir);

    float diff = max(dot(normal, light_dir), 0.0);
    float spec = pow(max(dot(normal, halfway), 0.0), u_specular_power);

    vec3 ambient = vec3(0.05);
    vec3 diffuse = vec3(0) * diff;
    vec3 specular = vec3(1.0, 0.8, 0.2) * spec;  // golden

    vec3 result = ambient + diffuse + specular;
    frag_color = vec4(result, 1.0);
}
