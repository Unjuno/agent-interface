"""Separate read-only X11 connection; sampled key state is not continuous truth."""
from __future__ import annotations
import json, threading, time
from pathlib import Path
from Xlib import XK, display

class KeymapMonitor:
    def __init__(self, name, out, keys=('a','d'), period_s=.01):
        self.name, self.out, self.keys, self.period_s = name, Path(out), keys, period_s
        self.stop, self.ready = threading.Event(), threading.Event()
        self.rows, self.error = [], None
        self.thread = threading.Thread(target=self._run, name='independent-keymap', daemon=False)
        self.thread.start()
        if not self.ready.wait(2): raise RuntimeError('keymap observer startup timeout')
        if self.error: raise RuntimeError(self.error)
    def _run(self):
        d = None
        try:
            d = display.Display(self.name)
            codes = [d.keysym_to_keycode(XK.string_to_keysym(k)) for k in self.keys]
            if not all(codes): raise RuntimeError('unmapped observer key')
            self.ready.set()
            while not self.stop.is_set():
                start = time.perf_counter_ns(); bits = list(d.query_keymap()); end = time.perf_counter_ns()
                self.rows.append(dict(started_ns=start, finished_ns=end, bitmap=bits,
                    keys=list(self.keys), keycodes=codes,
                    down=[k for k,c in zip(self.keys,codes) if bits[c//8] & (1 << (c%8))]))
                self.stop.wait(self.period_s)
        except Exception as e:
            self.error=repr(e); self.ready.set()
        finally:
            if d is not None: d.close()
    def close(self):
        self.stop.set(); self.thread.join(timeout=3)
        if self.thread.is_alive(): raise RuntimeError('keymap observer still alive')
        self.out.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in self.rows))
        if self.error: raise RuntimeError(self.error)
