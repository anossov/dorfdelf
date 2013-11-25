from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import bound

from panda3d.core import Point3, Vec3, Plane


class BlockPicker(DirectObject):
    SURFACE = 0
    SLICE = 1

    def __init__(self, world, app):
        self.world = world
        self.app = app
        self.picker = app.loader.loadModel('media/picked.egg')
        self.picker.reparentTo(app.render)
        self.picking_planes = [Plane(Vec3(0, 0, 1), Point3(0, 0, z + 1)) for z in self.world.zlevels()]
        self.picked = None
        self.mouse = app.mouseWatcherNode
        self.constraint = BlockPicker.SURFACE
        self.slice = None

        self.addTask(self.pick_block, "Pick block")
        self.accept('slice-changed', self.slice_changed)

    def pick_point(self, z, near, far):
        plane = self.picking_planes[z]
        pos3d = Point3()
        if plane.intersectsLine(pos3d,
                                self.app.render.getRelativePoint(self.app.cam, near),
                                self.app.render.getRelativePoint(self.app.cam, far)):
            return pos3d
        else:
            raise ValueError('Camera is coplanar to the picking plane')

    def slice_changed(self, slice, explore):
        if explore:
            self.constraint = BlockPicker.SURFACE
        else:
            self.constraint = BlockPicker.SLICE

        self.slice = slice

    def clamp_point(self, point, shift):
        px, py, pz = point
        sx, sy, sz = shift
        wx, wy, wz = self.world.size
        return (int(bound(px + sx, 0, wx - 1)),
                int(bound(py + sy, 0, wy - 1)),
                int(bound(pz + sz, 0, wz - 1)))

    def set_picked(self, point):
        if point != self.picked:
            self.picker.setPos(*point)
            self.picked = point
            self.app.messenger.send('block-hover', [point, self.world.get_block(*point)])

    def pick_block(self, task):
        if self.app.cc.moving:
            return task.again

        if self.mouse.hasMouse():
            mouse_pos = self.mouse.getMouse()

            near = Point3()
            far = Point3()
            self.app.camLens.extrude(mouse_pos, near, far)
            try:
                if self.constraint == BlockPicker.SURFACE:
                    for z in reversed(self.world.zlevels()):
                        point = self.pick_point(z, near, far)
                        picked = self.clamp_point(point, (0.5, 0.5, 0.5))
                        if not self.world.get_block(*picked).down.is_void:
                            self.set_picked(picked)
                            return task.again

                if self.constraint == BlockPicker.SLICE:
                    point = self.pick_point(self.slice, near, far)
                    picked = self.clamp_point(point, (0.5, 0.5, -0.5))
                    self.set_picked(picked)
                    return task.again
            except ValueError:
                pass

        return task.again

