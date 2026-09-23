#!/usr/bin/env python3
import argparse, json, os, socket, threading, time, tkinter as tk
from pathlib import Path

PRED_X = {"opening": 80, "closing": 180}
MID_X = 130
FINAL_X = {"Left": 80, "Right": 180}
EXPECTED = {"opening": "Right", "closing": "Left"}

p = argparse.ArgumentParser()
p.add_argument('--trajectory', choices=['opening','closing'], required=True)
p.add_argument('--socket', required=True)
p.add_argument('--truth', required=True)
a = p.parse_args()

sock_path = Path(a.socket); truth_path = Path(a.truth)
for q in (sock_path, truth_path):
    try: q.unlink()
    except FileNotFoundError: pass

root = tk.Tk()
root.title('AI Doorway')
root.geometry('320x200+0+0')
root.resizable(False, False)
canvas = tk.Canvas(root, width=320, height=200, bg='white', highlightthickness=0)
canvas.pack()
# Static doorway frame.
canvas.create_rectangle(60, 20, 260, 180, outline='black', width=4)
canvas.create_rectangle(65, 25, 255, 175, outline='#bbbbbb', width=1)
door = canvas.create_rectangle(PRED_X[a.trajectory], 35, PRED_X[a.trajectory]+60, 165,
                               fill='#404040', outline='#101010')
phase = {'name':'predecessor'}

def set_x(x):
    canvas.coords(door, x, 35, x+60, 165)
    canvas.update_idletasks(); canvas.update()

def on_key(ev):
    if ev.keysym not in FINAL_X:
        return
    t = time.monotonic_ns()
    set_x(FINAL_X[ev.keysym])
    result = {
        'trajectory': a.trajectory,
        'expected_action': EXPECTED[a.trajectory],
        'observed_action': ev.keysym,
        'correct': ev.keysym == EXPECTED[a.trajectory],
        'final_x': FINAL_X[ev.keysym],
        'event_ns': t,
    }
    truth_path.write_text(json.dumps(result, sort_keys=True)+'\n')

root.bind('<Left>', on_key); root.bind('<Right>', on_key)
root.after(100, root.focus_force)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(str(sock_path)); server.listen(4)

def serve():
    while True:
        try: conn,_ = server.accept()
        except OSError: return
        with conn:
            cmd = conn.recv(128).decode().strip()
            if cmd == 'PRE':
                root.after(0, lambda: (set_x(PRED_X[a.trajectory]), phase.update(name='predecessor')))
                conn.sendall(b'OK\n')
            elif cmd == 'CURRENT':
                root.after(0, lambda: (set_x(MID_X), phase.update(name='current')))
                conn.sendall(b'OK\n')
            elif cmd == 'FOCUS':
                root.after(0, root.focus_force); conn.sendall(b'OK\n')
            elif cmd == 'QUIT':
                conn.sendall(b'OK\n'); root.after(0, root.destroy); return
            else:
                conn.sendall(b'ERR\n')
threading.Thread(target=serve, daemon=True).start()
root.mainloop()
try: server.close()
except Exception: pass
