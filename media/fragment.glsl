#version 330


in Data {
    vec3 normal;
    vec4 eye;
    vec2 texcoord;
    vec4 color;
} DataIn;

uniform sampler2D p3d_Texture0;
uniform mat4 light;
uniform mat4 p3d_ModelViewMatrix;

out vec4 frag_color;

void main() {
    vec3 l_dir = (p3d_ModelViewMatrix * light[2]).xyz;
    vec4 spec = vec4(0.0);
    vec4 ambient = vec4(0.1, 0.1, 0.1, 1.0);
    vec4 specular = vec4(0.2, 0.2, 0.2, 1.0);
    float shininess = 128.0;
    // normalize both input vectors
    vec3 e = normalize(vec3(DataIn.eye));
    vec3 n = normalize(DataIn.normal);

    float intensity = max(dot(n, l_dir), 0.0);

    // if the vertex is lit compute the specular color
    if (intensity > 0.0) {
        // compute the half vector
        vec3 h = normalize(l_dir + e);
        // compute the specular term into spec
        float intSpec = max(dot(h, n), 0.0);
        spec = specular * pow(intSpec, shininess);
    }

    vec4 texColor = texture(p3d_Texture0, DataIn.texcoord);
    vec4 diffColor = intensity * texColor;
    vec4 ambColor = ambient * texColor;

    frag_color = max(diffColor + spec, ambColor);
//    frag_color = vec4(DataIn.normal, 1.0);
//    frag_color = light[2];
}
