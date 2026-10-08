"""Two-case deterministic queue-boundary probe against frozen InputOwner v10."""
import importlib.util
import json
import queue
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "dependencies" / "input_owner_v10.py"
RAW = HERE / "raw"


class FakeDisplay:
    def __init__(self, name):
        self.name = name
        self.down = set()
        self.events = []
        self.closed = False
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0)
        )

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        return None

    def close(self):
        self.closed = True


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")


def install_fake_xlib():
    saved = {name: sys.modules.get(name) for name in (
        "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
        "Xlib.ext", "Xlib.ext.xtest", "executor_v3",
    )}
    displays = []

    def module(name):
        out = types.ModuleType(name)
        sys.modules[name] = out
        return out

    xlib = module("Xlib")
    x = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonRelease=5, Button1Mask=256,
        AnyPropertyType=0,
    )
    xlib.X = x
    xk = module("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = module("Xlib.display")

    def new_display(name):
        item = FakeDisplay(name)
        displays.append(item)
        return item

    display.Display = new_display
    error = module("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = module("Xlib.ext")
    xtest = module("Xlib.ext.xtest")

    def fake_input(connection, event, code):
        connection.events.append([event, code])
        if event == x.KeyPress:
            connection.down.add(code)
        elif event == x.KeyRelease:
            connection.down.discard(code)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    executor = module("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    return saved, displays, x


def restore_modules(saved):
    for name, previous in saved.items():
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous


def run_case(case_id, overlap_stop):
    saved_modules, displays, x = install_fake_xlib()
    dequeue_seen = threading.Event()
    resume = threading.Event()
    original_queue = queue.Queue

    class BoundaryQueue(original_queue):
        def get(self, *args, **kwargs):
            item = super().get(*args, **kwargs)
            if item[0] == "release":
                dequeue_seen.set()
                if not resume.wait(2):
                    raise TimeoutError("release gate timed out")
            return item

    spec = importlib.util.spec_from_file_location(
        "input_owner_v10_" + case_id, SOURCE
    )
    owner_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner_module)
    queue.Queue = BoundaryQueue
    owner = None
    try:
        owner = owner_module.InputOwner(":fake")
        lease = Lease()
        admission = owner.call("down", lease, "a")
        reply, errors = [], []

        def send_release():
            try:
                reply.append(owner.call("release", lease))
            except BaseException as exc:
                errors.append(repr(exc))

        caller = threading.Thread(target=send_release)
        caller.start()
        if not dequeue_seen.wait(1):
            raise TimeoutError("release was not dequeued")
        if overlap_stop:
            owner.stop_requested.set()
        resume.set()
        caller.join(1)
        if caller.is_alive():
            raise TimeoutError("release caller did not return")
        if overlap_stop and not owner.stopped.wait(1):
            raise TimeoutError("owner did not stop")

        display = displays[0]
        records = [
            row.copy() for row in owner.records
            if row.get("event") == "owner_release"
        ]
        result = {
            "case_id": case_id,
            "overlap_stop_after_dequeue": overlap_stop,
            "candidate_exit_code": 0,
            "admission": admission,
            "release_reply_count": len(reply),
            "release_errors": errors,
            "owner_release_records_at_boundary": records,
            "xtest_events": display.events.copy(),
            "remaining_fake_keycodes_down": sorted(display.down),
            "owner_stopped_at_boundary": owner.stopped.is_set(),
        }
        RAW.joinpath(case_id + ".json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result
    finally:
        resume.set()
        if owner is not None:
            owner.close()
        queue.Queue = original_queue
        restore_modules(saved_modules)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name in ("baseline.json", "stop-overlap.json"):
        if RAW.joinpath(name).exists():
            raise FileExistsError(f"refusing to overwrite {name}")
    results = [run_case("baseline", False), run_case("stop-overlap", True)]
    for result in results:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
