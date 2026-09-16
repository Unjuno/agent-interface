import json, os, pathlib, time
from Xlib import X, XK, display
from Xlib.ext import xtest

out = pathlib.Path(os.environ['OUT'])
d = display.Display()
wid = int((out / 'window_id.txt').read_text().strip())
win = d.create_resource_object('window', wid)

def focus_id():
    q = d.get_input_focus()
    try:
        return int(q.focus.id)
    except Exception:
        return None

focus_before = focus_id()
win.set_input_focus(X.RevertToParent, X.CurrentTime)
d.sync()
time.sleep(0.075)
focus_after = focus_id()
if focus_after != wid:
    raise RuntimeError(f'focus mismatch: {focus_after} != {wid}')

keycode = int(d.keysym_to_keycode(XK.string_to_keysym('Right')))
ops = []

def edge(kind, event_type):
    before_ns = time.monotonic_ns()
    xtest.fake_input(d, event_type, keycode)
    d.sync()
    after_sync_ns = time.monotonic_ns()
    ops.append({'kind': kind, 'before_ns': before_ns, 'after_sync_ns': after_sync_ns})

for i in range(6):
    edge('press', X.KeyPress)
    time.sleep(0.190)
    edge('release', X.KeyRelease)
    if i < 5:
        time.sleep(0.010)

time.sleep(0.200)
keymap = d.query_keymap()
byte_index, bit_index = divmod(keycode, 8)
final_right_down = bool(keymap[byte_index] & (1 << bit_index))
result = {
    'window_id': wid,
    'focus_before': focus_before,
    'focus_after': focus_after,
    'keycode': keycode,
    'ops': ops,
    'final_right_down': final_right_down,
}
(out / 'controller.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
