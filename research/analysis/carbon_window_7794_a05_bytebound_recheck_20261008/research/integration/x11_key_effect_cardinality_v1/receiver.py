"""Cooperative ordinary Tk Entry receiver; stdin is observation/finish only."""
import json
import os
import sys
import time
import tkinter as tk


def send(record):
    record.update(pid=os.getpid(), ns=time.monotonic_ns())
    print(json.dumps(record, sort_keys=True), flush=True)


def main():
    expired = False
    root = tk.Tk()
    root.title("4032 private key-count fixture")
    root.geometry("360x100+20+20")
    entry = tk.Entry(root)
    entry.pack(padx=10, pady=20, fill="x")
    # A final bindtag records the value AFTER the ordinary Entry class binding.
    entry.bindtags((*entry.bindtags(), "EffectRecorder"))
    count = {"press": 0, "release": 0}

    def record(event, kind):
        count[kind] += 1
        send(dict(kind=kind, keycode=event.keycode, keysym=event.keysym,
                  char=event.char, x_time=event.time, state=event.state,
                  value=entry.get(), window=entry.winfo_id()))

    root.bind_class("EffectRecorder", "<KeyPress>", lambda e: record(e, "press"))
    root.bind_class("EffectRecorder", "<KeyRelease>", lambda e: record(e, "release"))
    root.update()
    entry.focus_force()

    def ready():
        send(dict(kind="ready", window=entry.winfo_id(), value=entry.get(),
                  tk_version=str(root.tk.call("info", "patchlevel")),
                  focus=str(root.focus_get())))

    def command(file, mask):
        line = file.readline()
        if line != "finish\n":
            raise RuntimeError("only the finish observation is accepted")
        root.deletefilehandler(sys.stdin)
        # The controller has completed a native event barrier before this command.
        # Defer to process already delivered Tk events; audit checks both streams.
        root.after(80, finish)

    def finish():
        send(dict(kind="final", window=entry.winfo_id(), value=entry.get(),
                  callback_counts=count.copy()))
        root.destroy()

    def deadline():
        nonlocal expired
        expired = True
        send(dict(kind="deadline", window=entry.winfo_id(), value=entry.get()))
        root.destroy()

    root.createfilehandler(sys.stdin, tk.READABLE, command)
    root.after(40, ready)
    root.after(4000, deadline)
    root.mainloop()
    if expired:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
