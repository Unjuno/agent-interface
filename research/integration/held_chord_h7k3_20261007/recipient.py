"""Private Xlib recipient; records received events and never synthesizes input."""
import json
import os
import select
import sys
import time
from Xlib import X, display


def main():
    d = display.Display(sys.argv[1])
    root = d.screen().root
    win = root.create_window(20, 20, 320, 160, 0, d.screen().root_depth,
                             X.InputOutput, X.CopyFromParent,
                             background_pixel=d.screen().white_pixel,
                             event_mask=X.KeyPressMask | X.KeyReleaseMask)
    win.set_wm_name('h7k3 private recipient')
    win.map()
    d.sync()
    events = []
    def drain():
        while d.pending_events():
            e = d.next_event()
            if e.type in (X.KeyPress, X.KeyRelease):
                row = dict(kind='press' if e.type == X.KeyPress else 'release',
                           keycode=int(e.detail), state=int(e.state),
                           server_time_ms=int(e.time), received_ns=time.monotonic_ns())
                events.append(row)
                journal.write(json.dumps(row, sort_keys=True) + '\n')
                journal.flush()
    with open(sys.argv[2], 'x', encoding='utf-8') as journal:
        print(json.dumps(dict(ready=True, pid=os.getpid(), window=win.id)), flush=True)
        while True:
            drain()
            readable, _, _ = select.select([sys.stdin, d.fileno()], [], [], 5)
            if sys.stdin not in readable:
                continue
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            d.sync()
            drain()
            print(json.dumps(dict(id=request['id'], events=events,
                                  observed_ns=time.monotonic_ns())), flush=True)
            if request['kind'] == 'stop':
                break
    win.destroy()
    d.sync()
    d.close()


if __name__ == '__main__':
    main()
