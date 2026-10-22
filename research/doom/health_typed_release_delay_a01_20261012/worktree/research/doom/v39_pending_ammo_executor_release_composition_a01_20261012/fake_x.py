"""Frozen fake-X modules: deterministic in-memory X server, no host input."""
import types
state=types.SimpleNamespace(keys=set(), buttons=set(), focus=42)
class _X:
    KeyPress=2; KeyRelease=3; ButtonPress=4; ButtonRelease=5; MotionNotify=6
    Button1Mask=256; Button2Mask=512; Button3Mask=1024; AnyPropertyType=0; IsViewable=2
class _XK:
    @staticmethod
    def string_to_keysym(name): return name
class _Root:
    id=1
    def query_pointer(self): return types.SimpleNamespace(mask=0,root_x=10,root_y=10)
    def get_geometry(self): return types.SimpleNamespace(width=800,height=600)
class _Screen:
    root=_Root()
class _Display:
    def __init__(self,name): self.name=name; self.closed=False
    def query_keymap(self):
        b=bytearray(32)
        for code in state.keys: b[code//8] |= 1 << (code%8)
        return bytes(b)
    def sync(self): pass
    def flush(self): pass
    def close(self): self.closed=True
    def keysym_to_keycode(self,keysym): return {'space':65,'d':40}.get(keysym,0)
    def get_input_focus(self): return types.SimpleNamespace(focus=types.SimpleNamespace(id=state.focus))
    def screen(self): return _Screen()
    def intern_atom(self,name): return 1
    def create_resource_object(self,*args): return _Root()
class _BadWindow(Exception): pass
class _BadDrawable(Exception): pass
Xlib=types.ModuleType('Xlib'); Xlib.X=_X; Xlib.XK=_XK
Xlib.display=types.SimpleNamespace(Display=_Display)
Xlib.error=types.SimpleNamespace(BadWindow=_BadWindow,BadDrawable=_BadDrawable)
Xlib.ext=types.ModuleType('Xlib.ext')
xtest=types.ModuleType('Xlib.ext.xtest')
def fake_input(d,event,detail=None,**kwargs):
    if event==_X.KeyPress: state.keys.add(detail)
    elif event==_X.KeyRelease: state.keys.discard(detail)
    elif event==_X.ButtonPress: state.buttons.add(detail)
    elif event==_X.ButtonRelease: state.buttons.discard(detail)
xtest.fake_input=fake_input
Xlib.ext.xtest=xtest
import sys
sys.modules['Xlib']=Xlib; sys.modules['Xlib.ext']=Xlib.ext; sys.modules['Xlib.ext.xtest']=xtest
