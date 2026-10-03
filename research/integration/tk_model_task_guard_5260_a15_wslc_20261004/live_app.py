"""Cooperative disposable Tk task. Snapshots are not sensor attestation.

No request can edit text or save: those effects require actual native keys.
Only the prospective private drift control can move app-owned focus.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk


def run(out, token, freeze_sha256, wanted, initial_target, initial_decoy):
    if not token or len(freeze_sha256) != 64 or any(c not in '0123456789abcdef'
                                                 for c in freeze_sha256):
        raise ValueError('Explicit task identity and source freeze required')
    out = Path(out)
    root = tk.Tk()
    root.title('Private live text task')
    root.geometry('520x350+40+40')
    root.resizable(False, False)
    font = ('DejaVu Sans', 22)
    tk.Label(root, text='Requested text: '+wanted, font=font).pack(pady=12)
    tk.Label(root, text='DECOY', font=('DejaVu Sans', 14)).pack()
    decoy = tk.Entry(root, font=font, width=18)
    decoy.pack()
    anchor = tk.Label(root, text='TARGET', font=('DejaVu Sans', 14))
    anchor.pack()
    target = tk.Entry(root, font=font, width=18)
    target.pack()
    tk.Label(root, text='Ctrl+S saves TARGET exactly once',
             font=('DejaVu Sans', 12)).pack(pady=10)
    # Initial controlled stimuli, never inferred repairs or native input evidence.
    target.insert(0, initial_target)
    decoy.insert(0, initial_decoy)
    events, saves, seen = [], [], set()
    pid = os.getpid()
    started = time.monotonic_ns()
    index = 1
    sequence = 0
    client_id = None

    def publish(name, value):
        with (out/name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write('\n')

    def geometry(widget):
        return {'id':widget.winfo_id(), 'x':widget.winfo_rootx(),
                'y':widget.winfo_rooty(), 'width':widget.winfo_width(),
                'height':widget.winfo_height()}

    def snapshot(nonce):
        nonlocal sequence
        capture_started = time.monotonic_ns()
        focus = root.focus_get()
        text, other = target.get(), decoy.get()
        sequence += 1
        return {'binding':{'pid':pid, 'token':token, 'root_id':client_id,
                           'target_id':target.winfo_id(), 'freeze_sha256':freeze_sha256},
                'nonce':nonce, 'sequence':sequence, 'started_ns':capture_started,
                'completed_ns':time.monotonic_ns(), 'target':text, 'decoy':other,
                'focus':'target' if focus is target else 'decoy' if focus is decoy else 'other'}

    def mark(kind, name, event):
        events.append({'kind':kind, 'widget':name, 'char':event.char,
                       'keysym':event.keysym, 'state':event.state,
                       'ns':time.monotonic_ns()})

    for name, widget in (('target', target), ('decoy', decoy)):
        widget.bind('<KeyPress>', lambda event, name=name: mark('KeyPress', name, event))
        widget.bind('<KeyRelease>', lambda event, name=name: mark('KeyRelease', name, event))

    def save(event):
        begin = time.monotonic_ns()
        value = {'schema':'issue5260-a15-task-file-v1', 'token':token,
                 'pid':pid, 'text':target.get()}
        blob = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'))+'\n').encode('utf-8')
        try:
            with (out/'task_result.json').open('xb') as stream:
                stream.write(blob)
                stream.flush()
                os.fsync(stream.fileno())
            saves.append({'status':'saved', 'started_ns':begin,
                          'completed_ns':time.monotonic_ns(), 'bytes':len(blob),
                          'sha256':hashlib.sha256(blob).hexdigest()})
        except FileExistsError:
            saves.append({'status':'refused_existing', 'started_ns':begin,
                          'completed_ns':time.monotonic_ns()})
        return 'break'

    root.bind('<Control-s>', save)

    def finish(reason):
        publish('app_result.json', {'token':token, 'pid':pid, 'started_ns':started,
            'ended_ns':time.monotonic_ns(), 'reason':reason,
            'target':target.get(), 'decoy':decoy.get(), 'events':events,
            'saves':saves, 'snapshot_count':sequence})
        root.destroy()

    def poll():
        nonlocal index
        if time.monotonic_ns()-started > 180_000_000_000:
            finish('bounded_app_deadline')
            return
        path = out/f'request-{index:06d}.json'
        if path.exists():
            try:
                request = json.loads(path.read_text())
            except json.JSONDecodeError:
                root.after(5, poll)
                return
            valid = (type(request) is dict and set(request) == {'operation','nonce','token'}
                     and request['token'] == token and type(request['nonce']) is str
                     and 0 < len(request['nonce']) <= 128 and request['nonce'] not in seen
                     and request['operation'] in ('snapshot', 'drift', 'finish'))
            if not valid:
                reply = {'status':'refused', 'reason':'request_identity_or_replay'}
            else:
                seen.add(request['nonce'])
                reply = {'status':'returned', 'nonce':request['nonce']}
                if request['operation'] == 'snapshot':
                    reply['snapshot'] = snapshot(request['nonce'])
                elif request['operation'] == 'drift':
                    decoy.focus_set()
                else:
                    publish(f'reply-{index:06d}.json', reply)
                    finish('explicit_finish')
                    return
            publish(f'reply-{index:06d}.json', reply)
            index += 1
        root.after(5, poll)

    def ready():
        nonlocal client_id
        root.focus_force()
        target.focus_set()
        target.icursor('end')
        root.update_idletasks()
        # Resolve this app's own Tk drawing child to its managed X11 ancestor.
        # Read-only ancestry, never title matching or authority issuance.
        from Xlib import display
        connection = display.Display()
        try:
            clients = connection.screen().root.get_full_property(
                connection.intern_atom('_NET_CLIENT_LIST'), 0)
            managed = set(int(value) for value in clients.value) if clients else set()
            window = connection.create_resource_object('window', root.winfo_id())
            for _ in range(16):
                if window.id in managed:
                    client_id = window.id
                    break
                window = window.query_tree().parent
            if client_id is None:
                raise RuntimeError('App-owned managed X11 client unavailable')
        finally:
            connection.close()
        surface = geometry(root)
        surface['id'] = client_id
        publish('ready.json', {'token':token, 'pid':pid, 'ready_ns':time.monotonic_ns(),
            'root':surface, 'tk_inner_id':root.winfo_id(),
            'target':geometry(target), 'decoy':geometry(decoy),
            'anchor':geometry(anchor), 'freeze_sha256':freeze_sha256})
        poll()

    root.after(150, ready)
    root.mainloop()


if __name__ == '__main__':
    run(*sys.argv[1:])
