from __future__ import division
import itertools
import math

import panda3d.core as core
from direct.showbase.DirectObject import DirectObject


class GeomBuilder(object):
    def __init__(self, name):
        self.total_vertices = 0
        self.name = name
        self.vertexformat = core.GeomVertexFormat.getV3n3t2()
        self.vertexdata = core.GeomVertexData(self.name, self.vertexformat, core.Geom.UHStatic)
        self.primitive = core.GeomTriangles(core.Geom.UHStatic)
        self.vertex_writer = core.GeomVertexWriter(self.vertexdata, 'vertex')
        self.normal_writer = core.GeomVertexWriter(self.vertexdata, 'normal')
        self.texcoord_writer = core.GeomVertexWriter(self.vertexdata, 'texcoord')
        self.geom = None

    def build(self):
        self.geom = core.Geom(self.vertexdata)
        self.geom.addPrimitive(self.primitive)
        gnode = core.GeomNode('{}-node'.format(self.name))
        gnode.addGeom(self.geom)
        return gnode


class Slice(core.NodePath):
    def __init__(self, world, z):
        core.NodePath.__init__(self, 'slice-{}'.format(z))

        self.world = world
        self.z = z

        self.chunks = {}
        self.hidden_chunks = {}

        self.setPos(0, 0, z)

        self.substances = [None] + [
            loader.loadTexture('media/{}.png'.format(name), anisotropicDegree=16, minfilter=core.Texture.FTLinearMipmapLinear)
            for name in ['dirt', 'stone']
        ]

        self.hiddentexture = loader.loadTexture('media/hidden.png', anisotropicDegree=16, minfilter=core.Texture.FTLinearMipmapLinear)
        self.hiddentexture.setWrapU(core.Texture.WMClamp)
        self.hiddentexture.setWrapV(core.Texture.WMClamp)

        blocks = 0
        for x, y in self.world.columns():
            b = self.world.get_block(x, y, self.z)
            if b.substance:
                blocks += 1

        chunks = max(1, blocks / 256)
        self.chunk_size = 2 ** int(math.log(self.world.width / math.sqrt(chunks), 2))

        self.updates = set()
        for cx, cy in itertools.product(range(self.world.width // self.chunk_size), range(self.world.height // self.chunk_size)):
            self.build_chunk(cx, cy)

        taskMgr.add(self.perform_updates, 'Slice update')

    def build_chunk(self, cx, cy):
        hbuilder = GeomBuilder('slice-{}-hidden'.format(self.z))
        builders = {}

        chunk_size = self.chunk_size
        block_getter = self.world.get_block

        for x, y in itertools.product(range(chunk_size), range(chunk_size)):
            b = block_getter(cx * chunk_size + x, cy * chunk_size + y, self.z)
            if not b.substance:
                continue

            if b.substance not in builders:
                builders[b.substance] = GeomBuilder('slice-{}-geom-{}'.format(self.z, b.substance))

            builder = builders[b.substance]
            if b.hidden:
                b.write_vertices(x, y, 0, hbuilder)
            else:
                b.write_vertices(x, y, 0, builder)

        chunk_size = self.chunk_size
        old = self.chunks.get((cx, cy))
        oldh = self.hidden_chunks.get((cx, cy))
        hide = True

        if old:
            for n in old:
                n.detachNode()
        if oldh:
            hide = oldh.isHidden()
            oldh.detachNode()

        nps = []
        for s, b in builders.items():
            np = self.attachNewNode(b.build())
            np.setPos(cx * chunk_size, cy * chunk_size, 0)
            np.setTexture(self.substances[s])
            nps.append(np)

        hnp = self.attachNewNode(hbuilder.build())
        hnp.setPos(cx * chunk_size, cy * chunk_size, 0)
        hnp.setTexture(self.hiddentexture)
        if hide:
            hnp.hide()
        else:
            hnp.show()

        self.chunks[(cx, cy)] = nps
        self.hidden_chunks[(cx, cy)] = hnp

    def update(self, x, y):
        cx, cy = x // self.chunk_size, y // self.chunk_size
        self.updates.add((cx, cy))

    def hide_hidden(self):
        for c in self.hidden_chunks.values():
            c.hide()

    def show_hidden(self):
        for c in self.hidden_chunks.values():
            c.show()

    def perform_updates(self, task):
        if self.updates:
            cx, cy = self.updates.pop()
            self.build_chunk(cx, cy)

        return task.cont


class WorldGeometry(DirectObject):
    def __init__(self, world):
        self.world = world
        self.node = core.NodePath('world')

        self.slices = []
        self.hidden_chunks = [[] for _ in range(self.world.depth)]

        for z in range(self.world.depth):
            slice = Slice(self.world, z)
            slice.reparentTo(self.node)
            self.slices.append(slice)

        self.accept('slice-changed', self.slice_changed)
        self.accept('block-update', self.block_update)

    def slice_changed(self, current_slice, explore):
        for i, s in enumerate(self.slices):
            d = abs(current_slice - i)
            if explore:
                s.show()
                s.clearColorScale()
                s.hide_hidden()
            else:
                if d == 0:
                    s.show_hidden()
                else:
                    s.hide_hidden()
                if i > current_slice or d > 5:
                    s.hide()
                else:
                    s.show()
                    if d:
                        v = 0.5 - d / 15.0
                        s.setColorScale(v, v, v, 1)
                    else:
                        s.clearColorScale()

    def block_update(self, pos):
        x, y, z = pos
        self.slices[z].update(x, y)
