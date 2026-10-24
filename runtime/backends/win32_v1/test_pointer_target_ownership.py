import ctypes
import unittest

from runtime.backends.win32_v1 import backend as native


class CursorOwnerAPI:
    def __init__(self, root_hwnd):
        self.root_hwnd = root_hwnd
        self.cursor = (10, 20)
        self.window_from_point_calls = []

    def IsWindow(self, hwnd):
        return True

    def SetCursorPos(self, x, y):
        self.cursor = (x, y)
        return True

    def GetCursorPos(self, pointer):
        point = ctypes.cast(pointer, ctypes.POINTER(native.POINT)).contents
        point.x, point.y = self.cursor
        return True

    def WindowFromPoint(self, point):
        self.window_from_point_calls.append((point.x, point.y))
        return 999

    def GetAncestor(self, hwnd, flags):
        return self.root_hwnd


class PointerTargetOwnershipTests(unittest.TestCase):
    def make_backend(self, hit_root):
        backend = native.Win32Backend.__new__(native.Win32Backend)
        backend.targets = {"calculator": 100}
        backend.user32 = CursorOwnerAPI(hit_root)
        backend.held_keys = {}
        backend.held_buttons = set()
        backend.pending_unicode_ups = set()
        backend.emissions = 0
        backend.focused_target = None
        backend.preflight = lambda program: None
        backend.focus = lambda target: setattr(backend, "focused_target", target)
        backend.pointer_button_calls = []
        backend.scroll_calls = []
        backend.pointer_button = lambda button, down: backend.pointer_button_calls.append(
            (button, down))
        backend.scroll = lambda dx, dy: backend.scroll_calls.append((dx, dy))
        backend.release_all = lambda: {"verified": True, "keys_down": [],
                                       "buttons_down": [], "keys_unknown": [],
                                       "buttons_unknown": []}
        return backend

    def program(self, down=True):
        return {"ops": [
            {"op": "focus", "target": "calculator"},
            {"op": "pointer_move", "frame": "screen_physical_px", "x": 10, "y": 20},
            {"op": "pointer_button", "button": "left", "down": down},
            {"op": "release_all"},
        ]}

    def test_dispatch_does_not_press_when_cursor_is_over_another_root_window(self):
        backend = self.make_backend(hit_root=200)

        with self.assertRaises(native.Win32ExecutionError):
            backend.execute(self.program(down=True))

        self.assertEqual(backend.pointer_button_calls, [])
        self.assertEqual(backend.user32.window_from_point_calls, [(10, 20)])

    def test_dispatch_presses_when_cursor_resolves_to_the_bound_target(self):
        backend = self.make_backend(hit_root=100)

        result = backend.execute(self.program(down=True))

        self.assertEqual(backend.pointer_button_calls, [("left", True)])
        self.assertEqual(result["releases"][-1]["verified"], True)

    def test_scroll_is_not_sent_to_an_occluding_window(self):
        backend = self.make_backend(hit_root=200)
        program = {"ops": [
            {"op": "focus", "target": "calculator"},
            {"op": "pointer_move", "frame": "screen_physical_px", "x": 10, "y": 20},
            {"op": "scroll", "dx": 0, "dy": 120},
            {"op": "release_all"},
        ]}

        with self.assertRaises(native.Win32ExecutionError):
            backend.execute(program)

        self.assertEqual(backend.scroll_calls, [])
        self.assertEqual(backend.user32.window_from_point_calls, [(10, 20)])

    def test_button_up_is_never_blocked_by_target_occlusion(self):
        backend = self.make_backend(hit_root=200)

        backend.execute(self.program(down=False))

        self.assertEqual(backend.pointer_button_calls, [("left", False)])
        self.assertEqual(backend.user32.window_from_point_calls, [])


if __name__ == "__main__":
    unittest.main()
