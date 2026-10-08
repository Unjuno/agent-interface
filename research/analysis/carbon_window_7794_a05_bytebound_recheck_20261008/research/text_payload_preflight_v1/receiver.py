"""Separate real Tk input consumer; stdin/stdout is harness-only control IPC."""
import json
import select
import sys
import tkinter as tk

root = tk.Tk()
root.title('Text payload conformance receiver')
entry = tk.Entry(root, width=75)
entry.pack(padx=15, pady=15)
root.clipboard_clear()
root.clipboard_append('PREVIOUS-αβ')
keys = []
entry.bind('<KeyPress>', lambda e: keys.append({'keycode':e.keycode, 'keysym':e.keysym, 'char':e.char}), add=True)

def respond():
    print(json.dumps({'text':entry.get(), 'keys':keys, 'xid':entry.winfo_id(),
                      'clipboard':root.clipboard_get()}, ensure_ascii=True), flush=True)

def poll():
    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if not line:
            root.destroy(); return
        req = json.loads(line)
        if req['op'] == 'reset':
            entry.delete(0, 'end')
            keys.clear()
            entry.focus_force()
        root.after(25, respond)
    root.after(5, poll)

root.after(10, poll)
root.mainloop()
