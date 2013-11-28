#version 330

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

out Data {
    vec3 normal;
    vec2 texcoord;
} DataOut;

void main()
{
    DataOut.normal = normalize(p3d_NormalMatrix * p3d_Normal);
    DataOut.normal = normalize(p3d_Normal);
    DataOut.texcoord = gl_MultiTexCoord0.st;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
