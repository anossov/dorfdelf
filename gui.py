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

        self.console = self.new_text(20, -60)
        self.console_errortext = self.new_text(40, -80)
        self.console_errortext.setFg((1, 0.5, 0.5, 1.0))

        self.accept('slice-changed', self.slice_changed)
        self.accept('block-hover', self.block_hover)
        self.accept('console-open', self.console.show)
        self.accept('console-close', self.console.hide)
        self.accept('console-update', self.update_console)
        self.accept('console-error', self.console_error)

    def slice_changed(self, slice, explore):
        self.current_slice.setText('Z-level: {}  explore: {}'.format(slice, explore))

    def block_hover(self, pos, b):
        self.block.setText('Block {}: {}'.format(pos, b))

    def update_console(self, chars):
        self.console.setText('CMD: ' + ''.join(chars))

    def console_error(self, e):
        self.console_errortext.setText(str(e))
        self.console_errortext.show()
        self.doMethodLater(5.0, self.console_errortext.hide, name='hide console error text', extraArgs=[])