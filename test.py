import direct.directbase.DirectStart
from direct.gui.OnscreenText import OnscreenText

from panda3d.core import *

loadPrcFileData("", "dump-generated-shaders 1")

base.setBackgroundColor(0.5, 0.5, 0.5)

t = OnscreenText(text='asdallaskjf')
t.reparentTo(base.aspect2d)

vertexformat = GeomVertexFormat.getV3()
vertexdata = GeomVertexData('MasterChunk', vertexformat, Geom.UHStatic)

vertex_writer = GeomVertexWriter(vertexdata, 'vertex')

for i in range(3):
    vertex_writer.addData3f(i, i, i)

primitive = GeomTriangles(Geom.UHStatic)
primitive.addVertices(0, 1, 2)

geom = Geom(vertexdata)
geom.addPrimitive(primitive)
gnode = GeomNode('gn')
gnode.addGeom(geom)

render.setShaderAuto()
base.render.attachNewNode(gnode)
m = base.loader.loadModel('media/dorfPH.egg')
m.reparentTo(base.render)

run()
