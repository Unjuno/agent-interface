"""Cooperative Tk fixture. Only XTEST can insert the task text."""
import json, os, sys, time, tkinter as tk
from pathlib import Path

session, journal_path = sys.argv[1:]
journal = open(journal_path, 'x', encoding='utf-8', buffering=1)
root = tk.Tk()
root.title('Owned nested-interrupt fixture')
root.geometry('420x180+0+0')
frames, retired = [], []
entries = {}

def log(kind, **fields):
    record = dict(kind=kind, ns=time.monotonic_ns(), pid=os.getpid(), **fields)
    journal.write(json.dumps(record, sort_keys=True)+'\n')
    return record

def entry(window, identity):
    v = tk.StringVar()
    e = tk.Entry(window, textvariable=v)
    e.pack(padx=20, pady=35)
    entries[identity] = (e, v)
    v.trace_add('write', lambda *_: log('value', widget=identity, value=v.get()))
    for kind in ('KeyPress', 'KeyRelease'):
        e.bind('<'+kind+'>', lambda ev, k=kind, i=identity: log(
            k, widget=i, key=ev.keysym, live=[f['id'] for f, _ in frames]), add='+')
    return e

base = entry(root, 'ROOT:1')

def focus():
    if frames:
        frame, w = frames[-1]
        w.grab_set()
        e = entries[frame['id']+':'+str(frame['generation'])][0]
    else:
        e = base
    e.focus_force()
    root.update()

def snapshot():
    return dict(root=entries['ROOT:1'][1].get(), retired=retired.copy(),
                live=[f.copy() for f, _ in frames], focus=str(root.focus_get()))

def reply(value):
    print(json.dumps(value, sort_keys=True), flush=True)

def handle(_fd, _mask):
    line = sys.stdin.readline()
    if not line:
        root.destroy()
        return
    cmd = json.loads(line)
    log('command', command=cmd)
    op = cmd['op']
    try:
        if op == 'open':
            name, generation = cmd['id'], cmd['generation']
            parent = frames[-1][0]['id']+':'+str(frames[-1][0]['generation']) if frames else 'ROOT:1'
            frame = dict(session=session, id=name, generation=generation, parent=parent)
            w = tk.Toplevel(frames[-1][1] if frames else root)
            w.title(name+':'+str(generation))
            w.geometry('350x160+30+30')
            entry(w, name+':'+str(generation))
            frames.append((frame, w))
            focus()
            value = log('opened', frame=frame)['frame']
        elif op == 'close':
            frame, w = frames.pop()
            assert frame['id'] == cmd['id']
            identity = frame['id']+':'+str(frame['generation'])
            retired.append(dict(frame=frame.copy(), text=entries[identity][1].get()))
            w.grab_release()
            w.destroy()
            focus()
            record = log('closed', frame=frame, text=retired[-1]['text'])
            value = dict(frame, closed_ns=record['ns'], status='RESOLVED')
        elif op == 'snapshot':
            root.update()
            value = snapshot()
            log('snapshot', value=value)
        elif op == 'quit':
            value = snapshot()
            log('quit', value=value)
            reply(value)
            root.destroy()
            return
        else:
            raise ValueError('unsupported fixture command')
        reply(value)
    except Exception as exc:
        log('error', error=repr(exc))
        reply({'error':repr(exc)})
        root.destroy()
        raise

root.createfilehandler(sys.stdin, tk.READABLE, handle)
focus()
log('ready', session=session, root_xid=root.winfo_id())
reply(dict(ready=True, pid=os.getpid(), session=session))
root.mainloop()
journal.close()
