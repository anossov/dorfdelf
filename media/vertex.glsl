#version 400

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec4 world_pos;

void main() {
    world_pos = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
