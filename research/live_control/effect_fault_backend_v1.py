"""Private X11 appearance replacement. Environment fixture, not policy logic."""
import json
import time
from Xlib import X, display
from cause_servo_session_v1 import Backend as Previous


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.fault_out = out
        self.perturb = display.Display(session.name)
        self.overlays = []
        self.injected = False

    def snapshot(self, identifier, index):
        if identifier == 'servo' and not self.injected:
            self.injected = True
            parent = self.perturb.create_resource_object('window', self.observed_pointer['surface'])
            gx, gy = self.observed_pointer['geometry'][:2]
            specs = [(592, 369, 56, 44, 0xffffff), (616, 373, 48, 36, 0xff0000)]
            for x, y, w, h, pixel in specs:
                win = parent.create_window(x-gx, y-gy, w, h, 0, X.CopyFromParent, X.InputOutput,
                                           X.CopyFromParent, background_pixel=pixel, override_redirect=True)
                win.map()
                self.overlays.append(win)
            self.perturb.sync()
            time.sleep(.04)
            (self.fault_out / 'environment-fault.json').write_text(json.dumps(dict(case='replacement', rectangles=specs,
                injected_ns=time.perf_counter_ns(), scope='environment-only appearance, not native document objects')) + '\n')
        return super().snapshot(identifier, index)

    def clear_overlay(self):
        if self.overlays:
            for win in self.overlays:
                win.destroy()
            self.overlays.clear()
            self.perturb.sync()
            time.sleep(.08)

    def execute(self, step, cancel, identifier, index):
        if identifier != 'servo':
            self.clear_overlay()
        return super().execute(step, cancel, identifier, index)

    def close(self):
        try:
            self.clear_overlay()
            self.perturb.close()
        finally:
            super().close()
