from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
import panda3d.core as core


class Designation(DirectObject):
    def __init__(self):
        self.model = loader.loadModel('media/models/picked.egg')
        self.shader = core.Shader.load(core.Shader.SLGLSL, 'media/shaders/vertex.glsl', 'media/shaders/flat.glsl')

    def add(self, w, x, y, z):
        n = core.NodePath('designation')
        n.setPos(x, y, z)
        n.setShader(self.shader)
        n.setShaderInput('color', core.Vec4(0.5, 1.0, 0.5, 0.5))
        self.model.instanceTo(n)

        messenger.send('designation-add', [x, y, z, n])
