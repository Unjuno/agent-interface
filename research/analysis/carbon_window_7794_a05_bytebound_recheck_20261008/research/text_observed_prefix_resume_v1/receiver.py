#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, socket, tkinter as tk
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--socket', type=Path, required=True)
    ap.add_argument('--ready', type=Path, required=True)
    args = ap.parse_args()
    if args.socket.exists():
        args.socket.unlink()

    root = tk.Tk()
    root.title('agent-interface-prefix-receiver')
    entry = tk.Entry(root, width=80)
    entry.pack(padx=20, pady=20)
    entry.focus_set()
    state = {'event_count': 0, 'events': [], 'swallow_at': None}

    def on_key(event):
        ch = event.char or ''
        if ch and ch.isprintable():
            state['event_count'] += 1
            state['events'].append({'n': state['event_count'], 'char': ch, 'keysym': event.keysym})
            if state['swallow_at'] == state['event_count']:
                return 'break'
        return None

    entry.bind('<KeyPress>', on_key, add=False)
    root.update_idletasks(); root.update()
    xid = entry.winfo_id()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(args.socket))
    server.listen(16)
    server.setblocking(False)

    args.ready.write_text(json.dumps({'xid': xid, 'socket': str(args.socket)})+'\n', encoding='utf-8')

    def handle(req: dict) -> dict:
        cmd = req.get('cmd')
        if cmd == 'get':
            return {'ok': True, 'text': entry.get(), 'event_count': state['event_count'], 'events': list(state['events'])}
        if cmd == 'reset':
            entry.delete(0, tk.END)
            state['event_count'] = 0
            state['events'] = []
            state['swallow_at'] = req.get('swallow_at')
            entry.focus_set()
            return {'ok': True}
        if cmd == 'set':
            entry.delete(0, tk.END)
            entry.insert(0, str(req.get('text', '')))
            return {'ok': True, 'text': entry.get()}
        if cmd == 'shutdown':
            root.after(1, root.destroy)
            return {'ok': True}
        return {'ok': False, 'error': 'unknown_command'}

    def poll():
        try:
            while True:
                conn, _ = server.accept()
                with conn:
                    raw = b''
                    while b'\n' not in raw:
                        part = conn.recv(65536)
                        if not part: break
                        raw += part
                    try:
                        req = json.loads(raw.split(b'\n',1)[0].decode('utf-8'))
                        res = handle(req)
                    except Exception as exc:
                        res = {'ok': False, 'error': type(exc).__name__+':'+str(exc)}
                    conn.sendall((json.dumps(res, ensure_ascii=False)+'\n').encode('utf-8'))
        except BlockingIOError:
            pass
        if root.winfo_exists():
            root.after(5, poll)

    root.after(5, poll)
    try:
        root.mainloop()
    finally:
        server.close()
        if args.socket.exists():
            args.socket.unlink()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
