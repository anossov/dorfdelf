import itertools
import random
import json
import sys

import panda3d.core as core
from direct.showbase.MessengerGlobal import messenger


DIRECTIONS = {
    'up': (0, 0, 1),
    'down': (0, 0, -1),
    'front': (0, 1, 0),
    'back': (0, -1, 0),
    'left': (-1, 0, 0),
    'right': (1, 0, 0)
}


def load_forms():
    models = loader.loadModel('media/forms.egg')

    yield Form('Void', [], [])

    for geomnode in models.findAllMatches('**/+GeomNode'):
        _, name = geomnode.getName().split(':')

        vertices = []
        indices = []

        geom = geomnode.node().getGeom(0)
        vdata = geom.getVertexData()

        vertex = core.GeomVertexReader(vdata, 'vertex')
        tex = core.GeomVertexReader(vdata, 'texcoord')
        normal = core.GeomVertexReader(vdata, 'normal')

        while not vertex.isAtEnd():
            v = vertex.getData3f()
            n = normal.getData3f()
            t = tex.getData2f()
            vertices.append((v, n, t))

        for prim in range(geom.getNumPrimitives()):
            primitive = geom.getPrimitive(prim).decompose()

            for p in range(primitive.getNumPrimitives()):
                for i in range(primitive.getPrimitiveStart(p), primitive.getPrimitiveEnd(p)):
                    vi = primitive.getVertex(i)
                    indices.append(vi)

        yield Form(name, vertices, indices)


class Form(object):
    def __init__(self, name, vertices, indices):
        self.name = name
        self.vertices = vertices
        self.indices = indices
        self.num_vertices = len(vertices)


class Substance(object):
    AIR = 0
    DIRT = 1
    STONE = 2
    '''
    moddable; minable, drop table, etc
    '''


class Block(object):
    __slots__ = ('form', 'substance', 'hidden', 'pos', 'world')

    FORMS = None

    def __init__(self, form, substance, hidden, pos, world):
        self.form = form
        self.substance = substance
        self.hidden = hidden
        self.pos = pos
        self.world = world

    @property
    def passable(self):
        return self.form.name == 'Void'

    @property
    def is_block(self):
        return self.form.name == 'Block'

    @property
    def is_void(self):
        return self.form.name == 'Void'

    @property
    def is_ramp(self):
        return self.form.name.startswith('Ramp')

    @property
    def up(self):
        return self.world.get_block(*(self.pos + (0, 0, 1)))

    @property
    def down(self):
        return self.world.get_block(*(self.pos + (0, 0, -1)))

    @property
    def right(self):
        return self.world.get_block(*(self.pos + (1, 0, 0)))

    @property
    def left(self):
        return self.world.get_block(*(self.pos + (-1, 0, 0)))

    @property
    def front(self):
        return self.world.get_block(*(self.pos + (0, 1, 0)))

    @property
    def back(self):
        return self.world.get_block(*(self.pos + (0, -1, 0)))

    def hides(self, direction):
        if self.is_block:
            return True
        if self.is_ramp and direction == (0, 0, 1):
            return True
        return False

    def __str__(self):
        return '{}/{}/{}'.format(self.form.name, self.substance, self.hidden)

    def __repr__(self):
        return str(self)


class NullBlock(Block):
    @property
    def is_block(self):
        return False

    @property
    def is_ramp(self):
        return False

    @property
    def is_void(self):
        return False

    @property
    def passable(self):
        return False

    def hides(self, direction):
        return True

    def __str__(self):
        return 'no block'


class World(object):
    def __init__(self, width, height, depth):
        self.forms = {f.name: f for f in load_forms()}
        print 'Registered forms: ', self.forms.keys()
        Block.FORMS = self.forms
        self.width = width
        self.height = height
        self.depth = depth

        self.size = core.Point3(self.width, self.height, self.depth)
        self.midpoint = core.Point3(self.width // 2, self.height // 2, self.depth // 2)

        self.blocks = [
            (self.forms['Void'], Substance.AIR, False)
            for x, y, z in itertools.product(range(self.width), range(self.height), range(self.depth))
        ]

    def __contains__(self, item):
        x, y, z = item
        if x < 0 or y < 0 or z < 0:
            return False
        if x >= self.width or y >= self.height or z >= self.depth:
            return False
        return True

    def _block_index(self, x, y, z):
        return int(x) * self.height * self.depth + int(y) * self.depth + int(z)

    def get_block(self, x, y, z):
        p = core.Point3(x, y, z)
        if p not in self:
            return NullBlock(None, None, False, p, self)

        f, s, h = self.blocks[self._block_index(x, y, z)]
        return Block(f, s, h, p, self)

    def set_block(self, x, y, z, form, substance, hidden, update_hidden=True):
        if (x, y, z) not in self:
            return False

        i = self._block_index(x, y, z)
        old = self.blocks[i]
        new = (form, substance, hidden)

        if old != new:
            self.blocks[i] = new
            messenger.send('block-update', [(x, y, z)])

            if update_hidden:
                for dx, dy, dz in DIRECTIONS.values():
                    self.update_hidden(x + dx, y + dy, z + dz)

    def update_hidden(self, x, y, z):
        b = self.get_block(x, y, z)
        if all(getattr(b, k).hides(d) for k, d in DIRECTIONS.items()):
            self.set_block(x, y, z, b.form, b.substance, True, False)
        else:
            self.set_block(x, y, z, b.form, b.substance, False, False)

    def all(self):
        for x, y, z in itertools.product(range(self.width), range(self.height), range(self.depth)):
            b = self.get_block(x, y, z)
            yield x, y, z, b

    def slice(self, z):
        for x, y in self.columns():
            yield x, y, self.get_block(x, y, z)

    def columns(self):
        for x, y in itertools.product(range(self.width), range(self.height)):
            yield x, y

    def zlevels(self):
        return range(self.depth)

    def make_ramp(self, x, y, z):
        b = self.get_block(x, y, z)

        if b.left.is_block and b.front.is_block:
            f, s = 'RampWN', b.left.substance
        elif b.front.is_block and b.right.is_block:
            f, s = 'RampNE', b.front.substance
        elif b.right.is_block and b.back.is_block:
            f, s = 'RampES', b.right.substance
        elif b.back.is_block and b.left.is_block:
            f, s = 'RampSW', b.back.substance
        elif b.left.is_block:
            f, s = 'RampW', b.left.substance
        elif b.right.is_block:
            f, s = 'RampE', b.right.substance
        elif b.back.is_block:
            f, s = 'RampS', b.back.substance
        elif b.front.is_block:
            f, s = 'RampN', b.front.substance
        else:
            return False

        self.set_block(x, y, z, self.forms[f], s, False)
        return True

    def generate(self):
        fbm = core.StackedPerlinNoise2(100, 100, 5, 2.01, 0.65)
        for x, y in self.columns():
            h = fbm.noise(x, y) * 20 + self.midpoint.z
            h2 = fbm.noise(x, y) * 7 + self.midpoint.z

            for z in range(int(max(h, h2))):
                i = self._block_index(x, y, z)
                if h < z < h2:
                    self.blocks[i] = (self.forms['Block'], Substance.DIRT, False)
                else:
                    self.blocks[i] = (self.forms['Block'], Substance.STONE, False)

        for x, y, z, b in self.all():
            if b.form.name == 'Void':
                if b.down.is_block:
                    self.make_ramp(x, y, z)

        for x, y, z, b in self.all():
            if b.form.name == 'Block':
                self.update_hidden(x, y, z)
                continue

    @staticmethod
    def load(fn):
        with open(fn) as f:
            data = json.load(f)

        w = World(*data['extents'])
        f = data['forms']

        for (x, y, z, b), datum in zip(w.all(), data['data']):
            i = w._block_index(x, y, z)
            form, substance, hidden = datum
            w.blocks[i] = (w.forms[f[form]], substance, hidden)

        return w

    def save(self, fn):
        forms = self.forms.keys()
        formmap = {f: i for i, f in enumerate(forms)}
        x, y, z = self.size
        data = {
            'extents': [int(x), int(y), int(z)],
            'forms': forms,
            'data': [
                (formmap[b.form.name], b.substance, int(b.hidden))
                for x, y, z, b in self.all()
            ]
        }
        with open(fn, 'w') as f:
            json.dump(data, f)