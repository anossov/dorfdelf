from itertools import chain
from direct.showbase.DirectObject import DirectObject


class Console(DirectObject):
    def __init__(self, app):
        self.app = app
        self.listening = False
        self.characters = []

    def add_char(self, char):
        charmap = {
            'space': ' ',
            'shift-=': '+',
        }
        mapped = charmap.get(char)
        if mapped is None:
            if char.startswith('shift-'):
                _, c = char.split('-', 1)
                mapped = c.upper()
            else:
                mapped = char

        self.characters.append(mapped)
        self.app.messenger.send('console-update', [self.characters])

    def del_char(self):
        if self.characters:
            self.characters.pop()

        self.app.messenger.send('console-update', [self.characters])

    def run_command(self):
        try:
            if self.characters:
                command = ''.join(self.characters).split()
                self.app.messenger.send('console-command', [command])
            self.close()
        except Exception as e:
            self.app.messenger.send('console-error', [e])

    def listen(self):
        self.listening = True
        self.app.messenger.send('console-open')
        self.app.messenger.send('console-update', [self.characters])
        self.accept('enter', self.run_command)
        self.accept('backspace', self.del_char)
        self.accept('backspace-repeat', self.del_char)
        chars = 'abcdefghijklmnopqrstuvwxyz01234567890-+='
        for c in chain(chars, ['shift-' + char for char in chars], ['space']):
            self.accept(c, self.add_char, [c])

    def close(self):
        self.listening = False
        self.characters = []
        self.app.messenger.send('console-close')
        self.app.messenger.send('console-update', [self.characters])
        self.ignoreAll()


