"""One disposable Tk app; the independent clock thread scores each deadline."""
from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path

OUT = Path(os.environ.get("OUT_DIR", "/out"))
TRIALS = json.loads(Path(os.environ["TRIALS_JSON"]).read_text())
EVENTS: list[dict] = []
EVENT_LOCK = threading.Lock()
DEADLINES: queue.Queue[tuple[dict, dict]] = queue.Queue()
ROOT = tk.Tk()
ROOT.title("6526 isolated save task")
LABEL = tk.Label(ROOT, text="Ready", width=48, height=5)
LABEL.pack()
BUTTON = tk.Button(ROOT, text="Commit task effect")
BUTTON.pack()
STATE = {"index": -1, "active": None, "observer_stop": None, "observer": None}


def record(kind: str, **fields: object) -> None:
    with EVENT_LOCK:
        EVENTS.append({"kind": kind, "mono_ns": time.monotonic_ns(), **fields})


def commit(trial: dict, scheduled_ns: int) -> None:
    if STATE["active"] is not trial:
        return
    t0 = time.monotonic_ns()
    path = OUT / f"effect-{trial['trial_id']}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"trial_id": trial["trial_id"], "value": trial["expected_value"]}, sort_keys=True)+"\n")
    os.replace(tmp, path)
    record("action_effect", trial_id=trial["trial_id"], action="button.invoke", effect_path=path.name,
           action_ns=t0, persisted_ns=time.monotonic_ns(), scheduled_ns=scheduled_ns)


def capture_loop(trial: dict, stop: threading.Event) -> None:
    while not stop.is_set():
        requested = time.monotonic_ns()
        path = OUT / "capture-current.xwd"
        try:
            with path.open("wb") as image:
                result = subprocess.run(["xwd", "-root", "-silent"], stdout=image, stderr=subprocess.PIPE,
                                        timeout=2, check=False)
            size = path.stat().st_size
            record("screenshot", trial_id=trial["trial_id"], request_ns=requested,
                   complete_ns=time.monotonic_ns(), exit_code=result.returncode, bytes=size)
        except Exception as exc:  # retained as a method failure, never retried by this loop
            record("screenshot_error", trial_id=trial["trial_id"], request_ns=requested,
                   complete_ns=time.monotonic_ns(), error=type(exc).__name__+":"+str(exc))
        finally:
            path.unlink(missing_ok=True)
        stop.wait(0.01)


def sham_loop(trial: dict, stop: threading.Event) -> None:
    while not stop.is_set():
        requested = time.monotonic_ns()
        record("sham", trial_id=trial["trial_id"], request_ns=requested,
               complete_ns=time.monotonic_ns())
        stop.wait(0.01)


def start_trial(index: int) -> None:
    if index >= len(TRIALS):
        record("run_complete", trials=len(TRIALS))
        ROOT.after(0, ROOT.destroy)
        return
    trial = TRIALS[index]
    STATE.update(index=index, active=trial)
    LABEL.configure(text=f"{trial['trial_id']} — {trial['schedule']} — {trial['arm']}")
    ROOT.update_idletasks()
    start_ns = time.monotonic_ns()
    record("trial_start", trial_id=trial["trial_id"], block=trial["block"], arm=trial["arm"],
           schedule=trial["schedule"], start_ns=start_ns, deadline_ms=trial["deadline_ms"],
           action_delay_ms=trial["action_delay_ms"])
    scheduled_ns = time.monotonic_ns()
    action_done = threading.Event()
    STATE["action_done"] = action_done
    BUTTON.configure(command=lambda item=trial, armed=scheduled_ns: commit(item, armed))
    def fire_action(item: dict = trial) -> None:
        if STATE["active"] is item:
            BUTTON.invoke()
        action_done.set()
    ROOT.after(trial["action_delay_ms"], fire_action)
    record("action_schedule", trial_id=trial["trial_id"], scheduled_ns=scheduled_ns,
           delay_ms=trial["action_delay_ms"], arm_delay_ns=scheduled_ns-start_ns)
    if trial["arm"] == "SCREENSHOT":
        stop = threading.Event()
        observer = threading.Thread(target=capture_loop, args=(trial, stop), name="screenshot-observer")
        STATE.update(observer_stop=stop, observer=observer)
        observer.start()
    elif trial["arm"] == "SHAM":
        stop = threading.Event()
        observer = threading.Thread(target=sham_loop, args=(trial, stop), name="sham-observer")
        STATE.update(observer_stop=stop, observer=observer)
        observer.start()
    else:
        STATE.update(observer_stop=None, observer=None)
    def independent_clock() -> None:
        deadline_ns = start_ns + trial["deadline_ms"] * 1_000_000
        time.sleep(max(0, (deadline_ns-time.monotonic_ns())/1_000_000_000))
        effect_path = OUT / f"effect-{trial['trial_id']}.json"
        snapshot_ns = time.monotonic_ns()
        payload = json.loads(effect_path.read_text()) if effect_path.exists() else None
        deadline = {"trial_id": trial["trial_id"], "deadline_ns": deadline_ns,
                    "snapshot_ns": snapshot_ns, "effect_present": payload is not None,
                    "effect_payload": payload}
        (OUT / f"deadline-{trial['trial_id']}.json").write_text(json.dumps(deadline, sort_keys=True)+"\n")
        DEADLINES.put((trial, deadline))

    threading.Thread(target=independent_clock, name="independent-deadline-clock", daemon=True).start()


def drain_deadlines() -> None:
    try:
        trial, deadline = DEADLINES.get_nowait()
    except queue.Empty:
        ROOT.after(1, drain_deadlines)
        return
    record("deadline_observed", **deadline)
    stop = STATE.get("observer_stop")
    observer = STATE.get("observer")
    if stop is not None:
        stop.set()
    if observer is not None:
        observer.join(timeout=2)
    def advance_when_action_finishes() -> None:
        if STATE["action_done"].is_set():
            ROOT.after(30, lambda: start_trial(STATE["index"]+1))
        else:
            ROOT.after(1, advance_when_action_finishes)
    advance_when_action_finishes()
    ROOT.after(1, drain_deadlines)


OUT.mkdir(parents=True, exist_ok=True)
ROOT.after(0, lambda: start_trial(0))
ROOT.after(1, drain_deadlines)
ROOT.mainloop()
with EVENT_LOCK:
    snapshot = list(EVENTS)
(OUT / "app-events.jsonl").write_text("".join(json.dumps(event, sort_keys=True)+"\n" for event in snapshot))
