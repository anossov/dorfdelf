# -*- encoding: utf-8 -*-

import random
from collections import Counter

from direct.showbase.ShowBase import ShowBase
from direct.showbase.PythonUtil import bound
from direct.gui.OnscreenImage import OnscreenImage


import panda3d.core as core
from panda3d.core import Point2, Point3, Vec3, Vec4, Mat4, Quat, VBase3D
from panda3d.core import loadPrcFileData

import world
import camera
import gui
import geometry

#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

class Dorfdelf(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        wp = core.WindowProperties()
        wp.setTitle("Dorfdelf")
        self.win.requestProperties(wp)

        self.render.setAntialias(core.AntialiasAttrib.MAuto)
        self.render.setShaderAuto()
        self.setBackgroundColor(0.1, 0.1, 0.1)


        #self.render.setAttrib(LightRampAttrib.makeHdr2())
        # Disable the camera trackball controls.
        self.disableMouse()

        ambientLight = core.AmbientLight('ambientLight')
        ambientLight.setColor(Vec4(.2, 0.2, 0.2, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)

        plight = core.DirectionalLight('plight')
        plight.setColor(Vec4(1.0, 1.0, 1.0, 1))
        plight.getLens().setNearFar(20, 1000)
        plight.getLens().setFilmSize(320, 320)
#        plight.setShadowCaster(True, 4096, 4096)
        plnp = self.render.attachNewNode(plight)
        self.render.setLight(plnp)

        self.world = world.World(64, 64, 100)
        self.world.generate()
        #self.world = world.World.load('test.world')

        self.world_geometry = geometry.WorldGeometry(self.world)

        plnp.setPos(self.world.width / 2 - 20, self.world.height / 2 + 30, 50)
        plnp.lookAt(self.world.width / 2, self.world.height / 2, 0)

        self.camLens.setFocalLength(1)
        self.camera.setPos(0, 0, 80)
        self.camera.lookAt(self.world.midpoint.x, self.world.midpoint.y, 80)
        self.cam.setPos(0, 0, 0)
        self.cam.setHpr(0, -45, 0)

        self.cc = camera.CameraController(self.world.size, self.taskMgr, self.mouseWatcherNode, self.camera, self.cam)
        self.gui = gui.GUI(self.pixel2d)
        self.world_geometry.node.setPos(0, 0, 0)
        self.world_geometry.node.reparentTo(self.render)

        self.explore_mode = True
        self.current_slice = int(self.world.midpoint.z)

        self.accept('e-repeat', self.change_slice, [-1])
        self.accept('q-repeat', self.change_slice, [1])
        self.accept('e', self.change_slice, [-1])
        self.accept('q', self.change_slice, [1])
        self.accept('tab', self.toggle_explore)

        self.accept('f1', self.world.save, ['test.world'])

        self.accept('mouse1', self.toggle_block)

        self.picked = self.loader.loadModel('media/picked.egg')
        self.picked.reparentTo(self.render)
        self.picking_plane = None

        tree = self.loader.loadModel('media/tree.egg')
        """
        for x, y in self.world.columns():
            z = self.world.depth - 1
            while z > 0:
                b = self.world.get_block(x, y, z)
                if b.is_block:
                    if random.random() > 0.95:
                        treeholder = self.render.attachNewNode('tree')
                        treeholder.setPos(x, y, z + 1)
                        tree.instanceTo(treeholder)
                if not b.is_void:
                    break
                z -= 1
        """
        self.dorfd = (1, 0, 0)
        self.dorf = self.loader.loadModel('media/dorfPH.egg')
        self.dorf.reparentTo(self.render)
        for z in reversed(range(self.world.depth)):
            b = self.world.get_block(32, 32, z)
            if not b.is_void:
                self.dorf.setPos(32, 32, z + 1)
                if not b.is_block:
                    b.update(self.world.forms['Block'], b.substance, False, (32, 32, z))
                break

        self.taskMgr.doMethodLater(0.5, self.movedorf, 'dorf')

        self.zmap = core.PNMImage(1, 256)
        colors = [
            VBase3D(0.7, 0.7, 0.9),
            VBase3D(0.4, 0.5, 0.1),
            VBase3D(0.6, 0.6, 0.6)
        ]

        def get_color(b):
            return colors[b.substance]

        for z in range(self.world.depth):
            types = Counter(get_color(self.world.get_block(x, y, z)) for x, y in self.world.columns())
            self.zmap.setXel(0, z, types.most_common(1)[0][0])

        tex = core.Texture()
        tex.load(self.zmap)
        tex.setMagfilter(core.Texture.FTNearest)
        tex.setMinfilter(core.Texture.FTLinearMipmapLinear)

        cm = core.CardMaker('z')
        cm.setFrame(0.98, 1, -1, 1)
        cm.setUvRange(Point2(1.0, 1.0),
                      Point2(0.0, 1.0 - self.world.depth / 256.0))
        self.zcard = self.render2d.attachNewNode(cm.generate())
        self.zcard.setTexture(tex)

        cm = core.CardMaker('zpointer')
        cm.setFrame(0, 0.05, 0, 1.0 / self.world.depth)
        self.zpointer = self.render2d.attachNewNode(cm.generate())
        self.zpointer.setColorScale(1.0, 0.0, 0.0, 0.4)

        self.change_slice(0)

        self.picked_block = None
        self.taskMgr.add(self.pick_block, "Pick block")
        print 'Init done'

    def toggle_explore(self):
        self.explore_mode = not self.explore_mode
        self.change_slice(0)

    def change_slice(self, n):
        if n:
            self.current_slice = bound(self.current_slice + n, 0, self.world.depth - 1)

        self.zpointer.setPos(0.95, 0.0, self.current_slice * 2.0 / self.world.depth - 1.0)

        self.messenger.send('slice-changed', [self.current_slice, self.explore_mode])
        self.picking_plane = core.Plane(Vec3(0, 0, 1), Point3(0, 0, self.current_slice + 1))

    def pick_block(self, task):
        if self.cc.moving:
            return task.again

        if self.mouseWatcherNode.hasMouse():
            mouse_pos = self.mouseWatcherNode.getMouse()
            pos3d = Point3()
            near = Point3()
            far = Point3()

            self.camLens.extrude(mouse_pos, near, far)
            if self.picking_plane.intersectsLine(pos3d, self.render.getRelativePoint(self.cam, near), self.render.getRelativePoint(self.cam, far)):
                worldpos = (int(bound(pos3d.x + 0.5, 0, self.world.width - 1)),
                            int(bound(pos3d.y + 0.5, 0, self.world.height - 1)),
                            int(bound(pos3d.z - 0.5, 0, self.world.depth - 1)))

                if worldpos != self.picked_block:
                    self.picked.setPos(*worldpos)
                    self.picked_block = worldpos
                    self.messenger.send('block-hover', [worldpos, self.world.get_block(*worldpos)])

        return task.again

    def toggle_block(self):
        if not self.picked_block:
            return

        b = self.world.get_block(*self.picked_block)

        if b.is_ramp:
            b.update(self.world.forms['Void'], 0, False, self.picked_block)
        elif b.is_void:
            b.update(self.world.forms['Block'], 1, False, self.picked_block)
        elif b.is_block:
            if not self.world.make_ramp(*self.picked_block):
                b.update(self.world.forms['Void'], 0, False, self.picked_block)

    def movedorf(self, task):
        c = self.dorf.getPos()

        if random.random() > 0.7 and c + self.dorfd in self.world:
            d = self.dorfd
        else:
            ds = [i for i in [(1, 0, 0), (0, 1, 0), (0, -1, 0), (-1, 0, 0)] if c + i in self.world]
            d = random.choice(ds)
            self.dorfd = d

        t = c + d

        self.dorf.lookAt(t)
        self.dorf.setPos(t)

        cwp = int(c.x), int(c.y), int(c.z)
        wp = int(t.x), int(t.y), int(t.z)
        cb = self.world.get_block(*cwp)
        b = self.world.get_block(*wp)
        if not b.is_void:
            if cb.is_ramp:
                self.dorf.setPos(self.dorf, (0, 0, -0.5))
            b.update(self.world.forms['Void'], 0, False, wp)
        else:
            if b.down.is_ramp:
                self.dorf.setPos(self.dorf, (0, 0, -0.5))
            if b.down.is_void:
                self.dorf.setPos(self.dorf, (0, 0, -1.0))

        return task.again


app = Dorfdelf()
app.run()