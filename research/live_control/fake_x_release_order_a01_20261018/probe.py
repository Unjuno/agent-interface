"""One-shot Fake X release-order construction; no display or input is opened."""
import argparse
import json
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend


class FakeServer:
    def __init__(self):
        self.down = set()
        self.events = []
        self.lock = threading.Lock()
        self.block_all = False
        self.server_entered = threading.Event()
        self.server_resume = threading.Event()

    def apply(self, connection, kind, detail):
        with self.lock:
            if kind == X.KeyPress:
                self.down.add(detail)
            elif kind == X.KeyRelease:
                self.down.discard(detail)
            else:
                raise AssertionError(f"unexpected Fake X event: {kind}")
            self.events.append({"phase": "apply", "connection": connection,
                                "kind": kind, "keycode": detail,
                                "down_after": sorted(self.down)})

    def keymap(self):
        with self.lock:
            bits = bytearray(32)
            for code in self.down:
                bits[code // 8] |= 1 << (code % 8)
            return bytes(bits)

    def snapshot(self):
        with self.lock:
            return sorted(self.down)


class FakeConnection:
    def __init__(self, name, server):
        self.name = name
        self.server = server
        self.pending = []
        self.io_lock = threading.Lock()
        self.sync_gate = None

    def send(self, kind, detail):
        with self.io_lock:
            self.pending.append((kind, detail))
            self.server.events.append({"phase": "queued", "connection": self.name,
                                      "kind": kind, "keycode": detail})

    def sync(self):
        with self.io_lock:
            if self.sync_gate is not None:
                entered, resume = self.sync_gate
                entered.set()
                if not resume.wait(5):
                    raise TimeoutError("Fake X sync harness was not resumed")
            if self.server.block_all:
                self.server.server_entered.set()
                if not self.server.server_resume.wait(5):
                    raise TimeoutError("Fake X server harness was not resumed")
            batch, self.pending = self.pending, []
            for kind, detail in batch:
                self.server.apply(self.name, kind, detail)

    def query_keymap(self):
        return self.server.keymap()


def backend(connection):
    obj = object.__new__(X11Backend)
    obj.d = connection
    obj.root = SimpleNamespace(query_pointer=lambda: SimpleNamespace(mask=0))
    obj.held_keycodes = {}
    obj.held_buttons = set()
    obj.emissions = 0
    obj._keycode = lambda key: 37
    obj._before_input_press = lambda: None
    return obj


def release_on_connection(obj, connection):
    """Research-only control-lane proposal; never used by production runtime."""
    tracked = dict(obj.held_keycodes)
    for code in list(tracked.values()):
        from runtime.backends.x11_v1 import backend as backend_module
        backend_module.xtest.fake_input(connection, X.KeyRelease, code)
        obj.emissions += 1
    connection.sync()
    view = backend(connection)
    keys = X11Backend._physical_keys_down(view, tracked)
    buttons = X11Backend._physical_buttons_down(view)
    obj.held_keycodes = {name: code for name, code in tracked.items() if name in keys}
    obj.held_buttons = set(buttons)
    return {"verified": not keys and not buttons, "keys_down": keys,
            "buttons_down": buttons}


def run_case(name):
    server = FakeServer()
    writer = FakeConnection("writer", server)
    control = FakeConnection("control", server)
    obj = backend(writer)
    outcomes, errors = [], []
    gates = []
    release_attempt = threading.Event()
    fake_input_calls = []
    send_gate = None

    def fake_input(connection, kind, detail):
        fake_input_calls.append({"connection": connection.name, "kind": kind,
                                 "keycode": detail})
        if kind == X.KeyRelease:
            release_attempt.set()
        if (send_gate is not None and connection is writer and
                kind == X.KeyPress):
            entered, resume = send_gate
            entered.set()
            if not resume.wait(5):
                raise TimeoutError("Fake X send harness was not resumed")
        connection.send(kind, detail)

    def invoke(fn, target):
        try:
            target.append(fn())
        except BaseException as error:
            errors.append(type(error).__name__ + ": " + str(error))

    press_thread = release_thread = None
    release_done = threading.Event()
    before = {}
    row = {"case": name, "mode": "optimized" if __debug__ is False else "normal"}
    module = __import__("runtime.backends.x11_v1.backend", fromlist=["xtest"])
    try:
        with patch.object(module.xtest, "fake_input", side_effect=fake_input):
            if name == "healthy":
                obj.key_state("CTRL", True)
                obj.key_state("CTRL", False)
                row.update(release={"verified": not server.snapshot(),
                                   "keys_down": server.snapshot(), "buttons_down": []})
            elif name == "same_connection_sync_block":
                entered, resume = threading.Event(), threading.Event()
                gates.append(resume)
                writer.sync_gate = (entered, resume)
                press_thread = threading.Thread(target=invoke,
                    args=(lambda: obj.key_state("CTRL", True), outcomes), daemon=True)
                press_thread.start()
                if not entered.wait(2):
                    raise AssertionError("writer did not enter blocked sync")
                release_thread = threading.Thread(target=invoke,
                    args=(obj.release_all, outcomes), daemon=True)
                release_thread.start()
                if not release_attempt.wait(2):
                    raise AssertionError("same-connection UP was not attempted")
                before = {"writer_alive": press_thread.is_alive(),
                          "release_alive": release_thread.is_alive(),
                          "release_returned": bool(outcomes),
                          "writer_queued": list(writer.pending),
                          "server_down": server.snapshot(),
                          "held_ledger": dict(obj.held_keycodes)}
                resume.set()
            elif name in ("separate_up_before_send", "separate_up_before_sync"):
                if name == "separate_up_before_send":
                    entered, resume = threading.Event(), threading.Event()
                    gates.append(resume)
                    send_gate = (entered, resume)
                else:
                    entered, resume = threading.Event(), threading.Event()
                    gates.append(resume)
                    writer.sync_gate = (entered, resume)
                press_thread = threading.Thread(target=invoke,
                    args=(lambda: obj.key_state("CTRL", True), outcomes), daemon=True)
                press_thread.start()
                if not entered.wait(2):
                    raise AssertionError("writer did not enter requested blocked boundary")
                release = release_on_connection(obj, control)
                before = {"release_returned": True, "release": release,
                          "writer_alive": press_thread.is_alive(),
                          "writer_queued": list(writer.pending),
                          "server_down": server.snapshot(),
                          "held_ledger": dict(obj.held_keycodes)}
                resume.set()
            elif name == "server_wide_stop":
                obj.key_state("CTRL", True)
                server.block_all = True
                server.server_resume.clear()
                release_thread = threading.Thread(target=invoke,
                    args=(lambda: release_on_connection(obj, control), outcomes), daemon=True)
                release_thread.start()
                if not server.server_entered.wait(2):
                    raise AssertionError("control connection did not reach server-wide stop")
                before = {"release_returned": bool(outcomes),
                          "release_alive": release_thread.is_alive(),
                          "control_queued": list(control.pending),
                          "server_down": server.snapshot(),
                          "held_ledger": dict(obj.held_keycodes)}
                server.block_all = False
                server.server_resume.set()
            else:
                raise ValueError(name)

            if press_thread is not None:
                press_thread.join(2)
                if press_thread.is_alive():
                    raise AssertionError("writer did not finish after test release")
            if release_thread is not None:
                release_thread.join(2)
                if release_thread.is_alive():
                    raise AssertionError("release path did not finish after test release")
    finally:
        for gate in gates:
            gate.set()
        server.server_resume.set()
        for thread in (press_thread, release_thread):
            if thread is not None:
                thread.join(2)

    row.update(before_resume=before, final_down=server.snapshot(),
               final_ledger=dict(obj.held_keycodes), writer_queued=list(writer.pending),
               control_queued=list(control.pending), writer_outcomes=outcomes,
               errors=errors, input_calls=fake_input_calls,
               server_events=server.events)
    if errors:
        raise AssertionError(f"{name}: {errors}")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite an existing outcome")
    rows = [run_case(name) for name in (
        "healthy", "same_connection_sync_block", "separate_up_before_send",
        "separate_up_before_sync", "server_wide_stop")]
    record = {"schema": "fake-x-release-order-a01-v1",
              "mode": "optimized" if __debug__ is False else "normal",
              "source_freeze": "SOURCE_FREEZE.json", "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": record["mode"],
        "cases": [{"case": row["case"], "before_resume": row["before_resume"],
                   "final_down": row["final_down"], "final_ledger": row["final_ledger"]}
                  for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
