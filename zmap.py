from collections import Counter

from direct.showbase.DirectObject import DirectObject

from panda3d.core import Point2, VBase3D, PNMImage, Texture, CardMaker


class ZMap(DirectObject):
    COLORS = [
        VBase3D(0.7, 0.7, 0.9),  # AIR
        VBase3D(0.4, 0.5, 0.1),  # DIRT
        VBase3D(0.6, 0.6, 0.6)   # STONE
    ]

    def __init__(self, world, app):
        self.world = world

        self.image = PNMImage(self.world.width, 256)

        for z in self.world.zlevels():
            for x in range(self.world.height):
                mix = sum([ZMap.COLORS[self.world.get_block(x, y, z).substance]
                          for y in range(self.world.height)], VBase3D(0.0))
                self.image.setXel(x, z, mix / float(self.world.height))

        self.texture = Texture()
        self.texture.load(self.image)
        self.texture.setMagfilter(Texture.FTNearest)
        self.texture.setMinfilter(Texture.FTNearest)

        cm = CardMaker('zmap')
        cm.setFrame(0.95, 1, -1, 1)
        cm.setUvRange(Point2(1.0, 1.0), Point2(0.0, 1.0 - self.world.depth / 256.0))
        self.zcard = app.render2d.attachNewNode(cm.generate())
        self.zcard.setTexture(self.texture)

        cm = CardMaker('zpointer')
        cm.setFrame(0, 0.05, 0, 1.0 / self.world.depth)
        self.zpointer = app.render2d.attachNewNode(cm.generate())
        self.zpointer.setColorScale(1.0, 0.0, 0.0, 0.4)

        self.accept('slice-changed', self.slice_changed)

    def slice_changed(self, slice, explore):
        self.zpointer.setPos(0.95, 0.0, slice * 2.0 / self.world.depth - 1.0)

