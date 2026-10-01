#!/usr/bin/env python3
from __future__ import annotations
import os, time, tkinter as tk
from Xlib import display

class ClipboardLease:
    def __init__(self, display_name: str):
        self.display_name=display_name
        os.environ['DISPLAY']=display_name
        self.root=tk.Tk(); self.root.withdraw(); self._closed=False
    def pump(self, seconds: float):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            self.root.update(); time.sleep(.005)
    def read_text(self) -> str:
        return self.root.selection_get(selection='CLIPBOARD', type='UTF8_STRING')
    def set_text(self, value: str) -> None:
        self.root.clipboard_clear(); self.root.clipboard_append(value); self.root.update()
    def owner_id(self):
        d=display.Display(self.display_name); owner=d.get_selection_owner(d.intern_atom('CLIPBOARD')); oid=getattr(owner,'id',None); d.close(); return oid
    def close(self):
        if not self._closed:
            self._closed=True; self.root.destroy()
