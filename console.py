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
        self.characters.append(charmap.get(char, char))
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
        for c in tuple('abcdefghijklmnopqrstuvwxyz01234567890-+') + ('space', 'shift-='):
            self.accept(c, self.add_char, [c])

    def close(self):
        self.listening = False
        self.characters = []
        self.app.messenger.send('console-close')
        self.app.messenger.send('console-update', [self.characters])
        self.ignoreAll()


