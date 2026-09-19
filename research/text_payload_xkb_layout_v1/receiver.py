#!/usr/bin/env python3
import json, os, queue, socket, sys, threading, tkinter as tk
path = sys.argv[1]
try: os.unlink(path)
except FileNotFoundError: pass
root = tk.Tk(); root.title('text-layout-receiver'); root.geometry('500x120+80+80')
value = tk.StringVar(); entry = tk.Entry(root, textvariable=value, font=('monospace', 18)); entry.pack(fill='both', expand=True); entry.focus_force(); root.update_idletasks()
q = queue.Queue()
def server():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.bind(path); s.listen(8)
    while True:
        c, _ = s.accept(); data = b''
        while not data.endswith(b'\n'):
            chunk = c.recv(65536)
            if not chunk: break
            data += chunk
        req = json.loads(data.decode()); box = {}; ev = threading.Event(); q.put((req, box, ev)); ev.wait(3)
        c.sendall((json.dumps(box, ensure_ascii=False) + '\n').encode()); c.close()
threading.Thread(target=server, daemon=True).start()
def poll():
    try:
        while True:
            req, box, ev = q.get_nowait(); op = req.get('op')
            if op == 'reset': value.set(''); entry.icursor(0); entry.focus_force(); box['ok'] = True
            elif op == 'get': box.update(ok=True, text=value.get())
            elif op == 'quit': box['ok'] = True; ev.set(); root.after(20, root.destroy); return
            else: box['error'] = 'bad_op'
            ev.set()
    except queue.Empty: pass
    root.after(5, poll)
root.after(5, poll)
print(json.dumps({'xid': root.winfo_id()}), flush=True)
root.mainloop()
