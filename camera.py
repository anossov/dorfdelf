import math

from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import bound

from panda3d.core import Vec3, Point2


class CameraController(DirectObject):
    def __init__(self, extents, taskmgr, mouse, body, eye):
        self.extents = extents
        self.body = body
        self.eye = eye

        self.mouse = mouse

        self.keys = {
            'w': False,
            's': False,
            'd': False,
            'a': False,
            'q': False,
            'e': False,
        }

        self.drag = None
        self.zoomdrag = None
        self.moving = False
        self.panning = False

        self.accept('d', self.key, ['d', True])
        self.accept('d-up', self.key, ['d', False])
        self.accept('w', self.key, ['w', True])
        self.accept('w-up', self.key, ['w', False])
        self.accept('a', self.key, ['a', True])
        self.accept('a-up', self.key, ['a', False])
        self.accept('s', self.key, ['s', True])
        self.accept('s-up', self.key, ['s', False])

        self.accept('mouse3', self.start_drag)
        self.accept('mouse3-up', self.end_drag)

        self.accept('mouse2', self.start_zoom)
        self.accept('mouse2-up', self.end_zoom)

        taskmgr.add(self.move_camera, "MoveCameraTask")

    def key(self, key, down):
        self.keys[key] = down

    def start_drag(self):
        if self.mouse.hasMouse():
            mouse_pos = Point2(self.mouse.getMouse())
            self.drag = mouse_pos, self.body.getH(), self.eye.getP()

    def end_drag(self):
        self.drag = None

    def start_zoom(self):
        if self.mouse.hasMouse():
            mouse_pos = Point2(self.mouse.getMouse())
            self.zoomdrag = mouse_pos, self.body.getZ()

    def end_zoom(self):
        self.zoomdrag = None

    def move_camera(self, task):
        self.panning = any(self.keys.values())
        self.moving = self.panning or self.drag or self.zoomdrag

        dt = globalClock.getDt()
        move_speed = 25
        if self.keys['w']:
            self.body.setY(self.body, dt * move_speed)
        if self.keys['s']:
            self.body.setY(self.body, -dt * move_speed)
        if self.keys['a']:
            self.body.setX(self.body, -dt * move_speed)
        if self.keys['d']:
            self.body.setX(self.body, dt * move_speed)

        if self.panning:
            pos = self.body.getPos()
            self.body.setPos(bound(pos.x, 0, self.extents.x),
                             bound(pos.y, 0, self.extents.y),
                             pos.z)

        if self.drag or self.zoomdrag:
            if self.mouse.hasMouse():
                end = self.mouse.getMouse()

                if self.drag:
                    start, h, p = self.drag
                    self.body.setH(h + (start.x - end.x) * 50)
                    self.eye.setP(bound(p - (start.y - end.y) * 50, -90, 45))

                if self.zoomdrag:
                    startzoom, z = self.zoomdrag

                    self.body.setZ(max(0, z + (startzoom.y - end.y) * 20))


        return task.cont
