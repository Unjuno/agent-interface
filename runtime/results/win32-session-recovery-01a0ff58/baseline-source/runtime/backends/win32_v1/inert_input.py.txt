from . import backend as native

class InputState:
    def __init__(self, stubborn=False, *, send_error=False, query_error=False):
        self.down = set()
        self.stubborn = stubborn
        self.send_error = send_error
        self.query_error = query_error
        self.events = []

    def SendInput(self, count, items, size):
        if count != 1:
            raise AssertionError('only single inert inputs allowed')
        item = items[0]
        if item.type == native.INPUT_KEYBOARD:
            vk = int(item.ki.wVk)
            down = not bool(item.ki.dwFlags & native.KEYEVENTF_KEYUP)
        elif item.type == native.INPUT_MOUSE:
            matches = [(vk, bool(item.mi.dwFlags & down_flag))
                       for down_flag, up_flag, vk in native.BUTTON_FLAGS.values()
                       if item.mi.dwFlags in (down_flag, up_flag)]
            if len(matches) != 1:
                raise AssertionError('only known inert button inputs allowed')
            vk, down = matches[0]
        else:
            raise AssertionError('unknown inert input')
        self.events.append({'send': vk, 'down': down})
        if self.send_error:
            raise native.Win32BackendError('inert send unavailable')
        if down:
            self.down.add(vk)
        elif not self.stubborn:
            self.down.discard(vk)
        return 1

    def GetAsyncKeyState(self, vk):
        self.events.append({'query': vk})
        if self.query_error:
            raise RuntimeError('inert read unavailable')
        return 0x8000 if vk in self.down else 0
