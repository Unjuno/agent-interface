"""Private live Tk fixture and separate read-only X11 observer; Issue #3943."""
import json
import os
import sys
import time
from pathlib import Path


def emit(obj):
    print(json.dumps(obj, sort_keys=True), flush=True)


def fixture(out):
    import tkinter as tk
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry('640x360+0+0')
    root.configure(background='#dddddd')
    counts = {'press': 0, 'release': 0, 'command': 0}
    journal = (out / 'app.jsonl').open('x', encoding='utf-8', buffering=1)
    revision = 0

    def record(kind, **data):
        journal.write(json.dumps({'kind': kind, 'ns': time.monotonic_ns(),
                                  'pid': os.getpid(), **data}, sort_keys=True) + '\n')
        journal.flush()

    marker = tk.Frame(root, background='#000000', borderwidth=0)
    marker.place(x=560, y=20, width=20, height=20)

    def effect():
        counts['command'] += 1
        marker.configure(background='#00ff00')
        record('command', count=counts['command'])

    button = tk.Button(root, text='COMMIT', command=effect, takefocus=False)
    button.place(x=90, y=110, width=120, height=60)
    # Add observational callbacks at the existing final "all" bindtag.
    # No Button class binding is replaced and no observer returns "break".
    def event(e):
        kind = str(e.type)
        if kind == '4':
            counts['press'] += 1
        elif kind == '5':
            counts['release'] += 1
        record('native', type=kind, widget=str(e.widget), x=e.x_root,
               y=e.y_root, state=e.state, serial=e.serial, send_event=e.send_event)
    for seq in ('<ButtonPress-1>', '<ButtonRelease-1>', '<Enter>', '<Leave>'):
        root.bind_all(seq, event, add=True)
    root.update()
    bindings = {s: root.bind_class('Button', s) for s in root.bind_class('Button')}
    record('ready', bindings=bindings, bindtags=list(button.bindtags()),
           tk=root.tk.call('info', 'patchlevel'), tk_package=root.tk.call('package', 'provide', 'Tk'))

    def snapshot():
        return {'pid': os.getpid(), 'button': button.winfo_id(),
                'marker': marker.winfo_id(), 'root': root.winfo_id(),
                'geometry': [button.winfo_rootx(), button.winfo_rooty(),
                             button.winfo_width(), button.winfo_height()],
                'revision': revision, 'counts': dict(counts)}
    emit({'ready': snapshot(), 'bindings': bindings})

    def command(fd, mask):
        nonlocal revision
        line = sys.stdin.readline()
        if not line:
            root.destroy()
            return
        request = json.loads(line)
        record('request', request=request)
        if request['op'] == 'move':
            button.place_configure(x=360, y=110)
            revision += 1
        elif request['op'] not in ('barrier', 'quit'):
            raise ValueError('unknown fixture operation')
        root.update()
        deadline = time.monotonic_ns() + 1_000_000_000
        def finish():
            needed = request.get('counts', {})
            if any(counts[k] < v for k, v in needed.items()):
                if time.monotonic_ns() >= deadline:
                    emit({'id': request['id'], 'error': 'NATIVE_EVENT_TIMEOUT', 'state': snapshot()})
                    return
                root.after(1, finish)
                return
            root.update_idletasks()
            state = snapshot()
            record('barrier', id=request['id'], state=state)
            emit({'id': request['id'], 'state': state})
            if request['op'] == 'quit':
                root.after_idle(root.destroy)
        root.after_idle(finish)
    root.createfilehandler(sys.stdin, tk.READABLE, command)
    root.mainloop()
    record('exit', counts=counts)
    journal.close()


def observer():
    from Xlib import X, display
    d = display.Display()
    root = d.screen().root
    visual = next(v for dep in d.screen().allowed_depths for v in dep.visuals
                  if v.visual_id == d.screen().root_visual)
    emit({'ready': True, 'pid': os.getpid()})
    for line in sys.stdin:
        req = json.loads(line)
        if req['op'] == 'quit':
            emit({'id': req['id'], 'stopped': True})
            break
        b = d.create_resource_object('window', req['button'])
        m = d.create_resource_object('window', req['marker'])
        g = b.get_geometry()
        origin = root.translate_coords(b, 0, 0)
        p = root.query_pointer()
        km = list(d.query_keymap())
        image = m.get_image(4, 4, 4, 4, X.ZPixmap, 0xffffffff)
        d.sync()
        emit({'id': req['id'], 'pid': os.getpid(), 'ns': time.monotonic_ns(),
              'button': req['button'], 'marker': req['marker'],
              'geometry': [origin.x, origin.y, g.width, g.height],
              'pointer': [p.root_x, p.root_y], 'mask': p.mask, 'keymap': km,
              'pixels_hex': (image.data.encode('latin1') if isinstance(image.data, str) else image.data).hex(),
              'data_type': type(image.data).__name__, 'depth': image.depth,
              'byte_order': d.display.info.image_byte_order,
              'masks': [visual.red_mask, visual.green_mask, visual.blue_mask]})
    d.close()


if __name__ == '__main__':
    if sys.argv[1] == 'fixture':
        fixture(Path(sys.argv[2]))
    elif sys.argv[1] == 'observer':
        observer()
    else:
        raise SystemExit('unknown actor')
