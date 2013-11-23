import panda3d.core as core
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText


class GUI(DirectObject):
    def new_text(self, x, y):
        return OnscreenText(text='',
                            pos=(x, y),
                            scale=20,
                            fg=(1, 1, 1, 1),
                            shadow=(0.3, 0.3, 0.3, 1.0),
                            align=core.TextNode.ALeft,
                            mayChange=True,
                            parent=self.parent)

    def __init__(self, parent):
        self.parent = parent

        self.current_slice = self.new_text(20, -20)
        self.block = self.new_text(20, -40)

        self.accept('slice-changed', self.slice_changed)
        self.accept('block-hover', self.block_hover)

    def slice_changed(self, slice, explore):
        self.current_slice.setText('Z-level: {}  explore: {}'.format(slice, explore))

    def block_hover(self, pos, b):
        self.block.setText('Block {}: {}'.format(pos, b))


