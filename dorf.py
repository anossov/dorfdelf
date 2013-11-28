import random
from itertools import count

import panda3d.core as core

from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.MessengerGlobal import messenger
from direct.particles.ParticleEffect import ParticleEffect


class Dorf(DirectObject):
    idgen = count()

    def __init__(self, pos, world):
        self.id = next(Dorf.idgen)
        self.world = world
        self.node = loader.loadModel('media/dorfPH.egg')
        self.text = core.TextNode('dorf')
        self.text.setText('Dorf {}'.format(self.id))
        self.text.setAlign(core.TextNode.ACenter)
        self.text.setTextColor(1, 1, 0.5, 1)
        self.text.setShadow(0.1, 0.1)
        self.text.setShadowColor(0, 0, 0, 0.8)
        self.textnode = self.node.attachNewNode(self.text)
        self.textnode.setBillboardPointEye()
        self.textnode.setPos(0, 0, 1.1)
        self.textnode.setScale(0.4)
        self.textnode.setDepthWrite(False)
        self.textnode.setDepthTest(False)
        self.textnode.setShaderOff()
        self.x = int(pos.x)
        self.y = int(pos.y)
        self.z = 0
        self.next = None
        self.dir = (1, 0)

        taskMgr.doMethodLater(0.5, self.move, 'Move dorf')

        self.set_z(int(pos.z))
        self.node.setPos(pos.x, pos.y, 0)

        self.particles = ParticleEffect()
        self.particles.loadConfig('media/sparks.ptf')
        self.particles.reparentTo(self.node)

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
            self.particles.setPos(0, 0, 0)
            self.particles.start()
            for p in self.particles.getParticlesList():
                p.induceLabor()
            #taskMgr.doMethodLater(1.0, self.particles.disable, 'stop particling', extraArgs=[])

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
