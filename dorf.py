import random

from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr


class Dorf(DirectObject):
    def __init__(self, pos, world):
        self.worldpos = pos
        self.world = world
        self.node = loader.loadModel('media/dorfPH.egg')

        self.node.setPos(self.worldpos)
        self.dir = (1, 0, 0)

        taskMgr.doMethodLater(0.5, self.move, 'Move dorf')

    def move(self, task):
        c = self.node.getPos()

        if random.random() > 0.4 and c + self.dir in self.world:
            d = self.dir
        else:
            ds = [i for i in [(1, 0, 0), (0, 1, 0), (0, -1, 0), (-1, 0, 0)] if c + i in self.world]
            d = random.choice(ds)
            self.dir = d

        t = c + d

        self.node.lookAt(t)
        self.node.setPos(t)

        cwp = int(c.x), int(c.y), int(c.z)
        wp = int(t.x), int(t.y), int(t.z)
        cb = self.world.get_block(*cwp)
        wx, wy, wz = wp
        b = self.world.get_block(wx, wy, wz)
        if not b.is_void:
            if cb.is_ramp:
                self.node.setPos(self.node, (0, 0, -0.5))
            self.world.set_block(wx, wy, wz, self.world.forms['Void'], 0, False)
        else:
            if b.down.is_ramp:
                self.node.setPos(self.node, (0, 0, -0.5))
            if b.down.is_void:
                self.node.setPos(self.node, (0, 0, -1.0))

        return task.again
