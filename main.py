# -*- encoding: utf-8 -*-

import itertools
import random

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import bound


import panda3d.core as core
from panda3d.core import Point2, Point3, Vec3, Vec4, Mat4, Quat, VBase3D
from panda3d.core import loadPrcFileData

import world
import camera
import gui
import geometry
import block_picker
import zmap
import console
import dorf
import tools

#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")


class Dorfdelf(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        wp = core.WindowProperties()
        wp.setTitle("Dorfdelf")
        self.win.requestProperties(wp)

        self.render.setAntialias(core.AntialiasAttrib.MAuto)
       # self.render.setShaderAuto()
        self.setBackgroundColor(0.1, 0.1, 0.1)

        self.disableMouse()

        shader = core.Shader.load(core.Shader.SLGLSL, 'media/vertex.glsl', 'media/fragment.glsl')
        self.render.setShader(shader)

        ambientLight = core.AmbientLight('ambientLight')
        ambientLight.setColor(Vec4(.2, 0.2, 0.2, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)

        plight = core.DirectionalLight('plight')
        plight.setColor(Vec4(1.0, 1.0, 1.0, 1))
        plight.getLens().setNearFar(20, 500)
        plight.getLens().setFilmSize(120, 120)
#       plight.setShadowCaster(True, 4096, 4096)
        plnp = self.render.attachNewNode(plight)
        self.render.setLight(plnp)
        self.render.setShaderInput('light', plnp)

        self.world = world.World(64, 64, 80)
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

        self.accept_keyboard()
        self.accept('mouse1', self.toggle_block)

        self.accept('console-command', self.console_command)

        self.dorfs = []
        self.tool = lambda w, x, y, z: None
        self.toolargs = ()
        self.tools = {
            'bomb': tools.bomb,
            'block': tools.block,
        }

        self.console = console.Console(self)
        self.picker = block_picker.BlockPicker(self.world, self)
        self.zmap = zmap.ZMap(self.world, self)

        self.change_slice(0)

        print 'Init done'

    def add_light(self):
        x, y = random.choice(list(self.world.columns()))
        for z in reversed(range(self.world.depth)):
            b = self.world.get_block(x, y, z)
            if not b.is_void:
                p = core.PointLight('pl-{}-{}-{}'.format(x, y, z))
                p.setAttenuation(Point3(0, 0, 0.4))
                pn = self.render.attachNewNode(p)
                pn.setPos(x, y, z + 3)
                self.render.setLight(pn)

    def add_dorf(self):
        x, y = random.choice(list(self.world.columns()))
        for z in reversed(range(self.world.depth)):
            b = self.world.get_block(x, y, z)
            if not b.is_void:
                d = dorf.Dorf(Point3(x, y, z + 1), self.world)
                self.dorfs.append(d)
                if not b.is_block:
                    self.world.set_block(x, y, z, self.world.forms['Block'], b.substance, False)
                break

    def accept_keyboard(self):
        self.accept('e-repeat', self.change_slice, [-1])
        self.accept('q-repeat', self.change_slice, [1])
        self.accept('e', self.change_slice, [-1])
        self.accept('q', self.change_slice, [1])
        self.accept('tab', self.toggle_explore)
        self.accept('f1', self.world.save, ['test.world'])

        self.accept('enter', self.open_console)
        self.accept('console-close', self.accept_keyboard)

    def ignore_keyboard(self):
        self.ignore('e')
        self.ignore('e-repeat')
        self.ignore('q-repeat')
        self.ignore('q')
        self.ignore('tab')
        self.ignore('f1')
        self.ignore('enter')

    def open_console(self):
        self.console.listen()
        self.ignore_keyboard()

    def console_command(self, args):
        args = list(args)
        cmd = args.pop(0)

        if cmd == 'explore':
            self.toggle_explore()
        if cmd == 'slice':
            n = args[0]
            self.change_slice(int(n), rel=args[0][0] in '-+')
        if cmd == 'wire':
            self.toggleWireframe()
        if cmd == 'texmem':
            self.toggleTexMem()
        if cmd == 'texture':
            self.toggleTexture()
        if cmd == 'dorf':
            n = 1
            if args:
                n = int(args[0])
            for _ in range(n):
                self.add_dorf()
        if cmd == 'analyze':
            self.render.analyze()
        if cmd == 'ls':
            self.render.ls()
        if cmd == 'generate':
            self.world.generate()
            self.world_geometry.update_all()

        if cmd == 't':
            t = args.pop(0)
            self.tool = self.tools[t]
            self.toolargs = args

        if cmd == 'light':
            self.add_light()

    def toggle_explore(self):
        self.explore_mode = not self.explore_mode
        self.change_slice(0)

    def change_slice(self, n, rel=True):
        s = self.current_slice + n if rel else n
        self.current_slice = bound(s, 0, self.world.depth - 1)
        self.messenger.send('slice-changed', [self.current_slice, self.explore_mode])

    def toggle_block(self):
        if not self.picker.picked:
            return

        x, y, z = self.picker.picked

        try:
            self.tool(self.world, x, y, z, *self.toolargs)
        except Exception as e:
            print e


app = Dorfdelf()
app.run()
