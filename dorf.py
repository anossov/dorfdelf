import random

from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.MessengerGlobal import messenger


class Dorf(DirectObject):
    def __init__(self, pos, world):
        self.world = world
        self.node = loader.loadModel('media/dorfPH.egg')

        self.x = int(pos.x)
        self.y = int(pos.y)
        self.z = 0
        self.next = None
        self.dir = (1, 0)

        taskMgr.doMethodLater(0.5, self.move, 'Move dorf')

        self.set_z(int(pos.z))
        self.node.setPos(pos.x, pos.y, 0)

    def set_z(self, z):
        self.z = z
        messenger.send('entity-z-change', [self])

    def move(self, task):
        if self.next:
            self.x, self.y, z = self.next
            self.node.setPos(self.x, self.y, 0)
            if self.z != z:
                self.set_z(z)

        b = self.world.get_block(self.x, self.y, self.z)
        if b.is_ramp:
            self.node.setPos(self.x, self.y, 0.5)
        else:
            self.node.setPos(self.x, self.y, 0.0)

        if b.is_block:
            self.world.set_block(self.x, self.y, self.z, self.world.forms['Void'], 0, False)

        self.set_next()
        self.node.lookAt(self.next[0], self.next[1], 0)

        return task.again

    def set_next(self):
        x, y, z = self.x + self.dir[0], self.y + self.dir[1], self.z
        if (x, y, z) not in self.world or random.random() < 0.4:
            ds = [((dx, dy), (self.x + dx, self.y + dy, self.z)) for dx, dy in [(1, 0), (0, 1), (0, -1), (-1, 0)]]
            self.dir, np = random.choice([(d, n) for d, n in ds if n in self.world])
            x, y, z = np

        b = self.world.get_block(x, y, z)

        if b.is_void and not b.down.is_block:
            z -= 1

        self.next = (x, y, z)
