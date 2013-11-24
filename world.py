import itertools
import random
import json

import panda3d.core as core
from direct.showbase.MessengerGlobal import messenger

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
    __slots__ = ('form', 'substance', 'hidden', 'neighbours')

    FORMS = None

    def __init__(self, form, substance=Substance.AIR, hidden=False):
        self.form = form
        self.substance = substance
        self.hidden = hidden
        self.neighbours = {}

    def write_vertices(self, x_offset, y_offset, z_offset, builder):
        if self.hidden:
            form = Block.FORMS['Hidden']
        else:
            form = self.form

        for v, n, t in form.vertices:
            builder.vertex_writer.addData3f(v[0] + x_offset, v[1] + y_offset, v[2] + z_offset)
            builder.normal_writer.addData3f(*n)
            builder.texcoord_writer.addData2f(*t)

        for i in form.indices:
            builder.primitive.addVertex(builder.total_vertices + i)

        builder.total_vertices += form.num_vertices

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
        return self.neighbours[(0, 0, 1)]

    @property
    def down(self):
        return self.neighbours[(0, 0, -1)]

    @property
    def right(self):
        return self.neighbours[(1, 0, 0)]

    @property
    def left(self):
        return self.neighbours[(-1, 0, 0)]

    @property
    def front(self):
        return self.neighbours[(0, 1, 0)]

    @property
    def back(self):
        return self.neighbours[(0, -1, 0)]

    def hides(self, direction):
        if self.is_block:
            return True
        if self.is_ramp and direction == (0, 0, 1):
            return True
        return False

    def update(self, form, substance, hidden, coords=None):
        old = (self.form, self.substance, self.hidden)
        self.form = form
        self.substance = substance
        self.hidden = hidden

        if coords is not None:
            if old != (form, substance, hidden):
                messenger.send('block-update', [coords])
                for d, n in self.neighbours.items():
                    n.update_hidden((coords[0] + d[0], coords[1] + d[1], coords[2] + d[2]))

    def update_hidden(self, coords=None):
        if all(n.hides(d) for d, n in self.neighbours.items()):
            self.update(self.form, self.substance, True, coords)
        else:
            self.update(self.form, self.substance, False, coords)

    def __str__(self):
        return '{}/{}/{}'.format(self.form.name, self.substance, self.hidden)

    def __repr__(self):
        return str(self)


class NullBlock(Block):
    def __init__(self):
        self.neighbours = {}

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

    def update(self, form, substance, hidden, coords=None):
        return None

    def update_hidden(self, coords=None):
        return None

    def __str__(self):
        return 'no block'


class World(object):
    def __init__(self, width, height, depth):
        self.forms = {f.name: f for f in load_forms()}
        print 'Registered forms: ', self.forms.keys()
        Block.FORMS = self.forms
        self.nullblock = NullBlock()
        self.width = width
        self.height = height
        self.depth = depth

        self.size = core.Point3(self.width, self.height, self.depth)
        self.midpoint = core.Point3(self.width // 2, self.height // 2, self.depth // 2)

        self.blocks = [
            [
                [Block(self.forms['Void']) for _ in range(self.depth)]
                for _ in range(self.height)
            ] for _ in range(self.width)
        ]

        for x, y, z, b in self.all():
            b.neighbours = {
                (dx, dy, dz): self.get_block(x + dx, y + dy, z + dz)
                for dx, dy, dz in [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1),
                (-1, -1, 0), (1, 1, 0), (1, -1, 0), (-1, 1, 0)]
            }

    def __contains__(self, item):
        x, y, z = item
        if x < 0 or y < 0 or z < 0:
            return False
        if x >= self.width or y >= self.height or z >= self.depth:
            return False
        return True

    def get_block(self, x, y, z):
        if x < 0 or y < 0 or z < 0:
            return self.nullblock
        try:
            return self.blocks[x][y][z]
        except IndexError:
            return self.nullblock

    def all(self):
        for x, y, z in itertools.product(range(self.width), range(self.height), range(self.depth)):
            b = self.get_block(x, y, z)
            yield x, y, z, b

    def columns(self):
        for x, y in itertools.product(range(self.width), range(self.height)):
            yield x, y

    def zlevels(self):
        return range(self.depth)

    def make_ramp(self, x, y, z, generation=False):
        b = self.get_block(x, y, z)
        c = None if generation else (x, y, z)
        if b.left.is_block and b.front.is_block:
            b.update(self.forms['RampWN'], b.left.substance, False, c)
        elif b.front.is_block and b.right.is_block:
            b.update(self.forms['RampNE'], b.front.substance, False, c)
        elif b.right.is_block and b.back.is_block:
            b.update(self.forms['RampES'], b.right.substance, False, c)
        elif b.back.is_block and b.left.is_block:
            b.update(self.forms['RampSW'], b.back.substance, False, c)
        elif b.left.is_block:
            b.update(self.forms['RampW'], b.left.substance, False, c)
        elif b.right.is_block:
            b.update(self.forms['RampE'], b.right.substance, False, c)
        elif b.back.is_block:
            b.update(self.forms['RampS'], b.back.substance, False, c)
        elif b.front.is_block:
            b.update(self.forms['RampN'], b.front.substance, False, c)
        else:
            return False
        return True

    def generate(self):
        fbm = core.StackedPerlinNoise2(100, 100, 5, 2.01, 0.65)
        for x, y in self.columns():
            h = fbm.noise(x, y) * 20 + self.midpoint.z
            h2 = fbm.noise(x, y) * 7 + self.midpoint.z

            for z in range(int(max(h, h2))):
                b = self.get_block(x, y, z)
                if h < z < h2:
                    b.update(self.forms['Block'], Substance.DIRT, False)
                else:
                    b.update(self.forms['Block'], Substance.STONE, False)

        for x, y, z, b in self.all():
            if b.form.name == 'Void':
                if b.down.is_block:
                    self.make_ramp(x, y, z, True)

        for x, y, z, b in self.all():
            if b.form.name == 'Block':
                b.update_hidden()
                continue

    @staticmethod
    def load(fn):
        with open(fn) as f:
            data = json.load(f)

        w = World(*data['extents'])
        f = data['forms']

        for (x, y, z, b), datum in zip(w.all(), data['data']):
            form, substance, hidden = datum
            b.update(w.forms[f[form]], substance, hidden)

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