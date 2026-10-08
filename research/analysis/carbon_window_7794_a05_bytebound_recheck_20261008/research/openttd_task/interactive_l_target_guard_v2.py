"""Run the seed991004 L fixture through the target/guard X11 backend."""
import argparse
import contextlib
import hashlib
import json
import shutil
import sys
import threading
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from executor_v3 import Executor
from guarded_l_score_v1 import score
from lease import Expired
from session_v25 import Backend, suite


SAVE = HERE / "results/l-geometry-02/baseline.sav"
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--controller", choices=["scripted"], required=True)
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    assert sha(SAVE) == SAVE_SHA
    live = HERE.parent / "live_control"
    sources = [Path(__file__).resolve(), HERE / "guarded_l_score_v1.py",
               *sorted((HERE / "observer_l_v1").glob("*.nut"))]
    sources += [live / name for name in [
        "session_v25.py", "local_target_guard_postcondition_v1.py",
        "session_v24.py", "local_displacement_postcondition_v1.py", "visual_anchor.py",
        "session_v23.py", "session_v22.py", "session_v21.py", "session_v20.py",
        "session_v19.py", "session_v18.py", "session_v17.py", "session_v16.py",
        "session_v15.py", "session_v14.py", "session_v13.py", "session_v12.py",
        "session_v11.py", "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py"]]
    (args.out / "manifest.json").write_text(json.dumps({
        "scope": "scripted target/guard controller; seed991004 changed-save five-tile L objective; independent dynamic guard score",
        "save_sha256": SAVE_SHA,
        "sources": {str(path.relative_to(HERE.parent)): sha(path) for path in sources}},
        indent=2) + "\n")
    lock = threading.Lock()
    session = backend = engine = None

    def emit(record):
        with lock:
            record["emitted_ns"] = time.perf_counter_ns()
            line = json.dumps(record)
            with (args.out / "events.jsonl").open("a") as stream:
                stream.write(line + "\n")
            print(line, flush=True)

    try:
        with (args.out / "setup.txt").open("w") as setup, contextlib.redirect_stdout(setup):
            session = suite.Session()
            root = args.root / "root/usr"
            libraries = root / "lib/x86_64-linux-gnu"
            session.env.update(LD_LIBRARY_PATH=f"{libraries}:{libraries}/pulseaudio",
                               SDL_VIDEODRIVER="x11", SDL_AUDIODRIVER="dummy",
                               LIBGL_ALWAYS_SOFTWARE="1")
            data = Path(session.env["XDG_DATA_HOME"]) / "openttd"
            data.mkdir()
            for source in (root / "share/games/openttd").iterdir():
                if source.name != "game":
                    (data / source.name).symlink_to(source)
            shutil.copytree(root / "share/games/openttd/game", data / "game")
            shutil.copytree(HERE / "observer_l_v1", data / "game/interface_task")
            config = args.out / "openttd.cfg"
            config.write_text("[game_scripts]\nInterfaceTask = \n")
            with (args.out / "game-stdout.txt").open("w") as stdout, \
                    (args.out / "game-stderr.txt").open("w") as stderr:
                session.spawn([str(root / "games/openttd"), "-c", str(config),
                               "-d", "script=4", "-s", "null", "-m", "null",
                               "-r", "1024x720", "-g", str(SAVE)],
                              cwd=args.out, stdout=stdout, stderr=stderr)
            session._wait(lambda: "AIT_READY" in (args.out / "game-stderr.txt").read_text(),
                          40, "saved changed-geometry L observer task ready")
            session.wait_window("OpenTTD")
            session.focus("OpenTTD")
            backend = Backend(session, args.out, emit)
        engine = Executor(backend, emit)
        emit({"event": "ready", "task": "Build the five-tile L from A through B to C and preserve all guard tiles."})
        backend.snapshot("initial", 0)
        for line in sys.stdin:
            try:
                command = json.loads(line)
                emit({"event": "command", "command": command})
                if command["op"] == "submit":
                    engine.submit(command["id"], command["steps"],
                                  command["expected_sequence"], command["valid_until_ns"])
                elif command["op"] == "clock":
                    emit({"event": "clock", "runtime_ns": time.perf_counter_ns(),
                          "sequence": backend.sequence})
                elif command["op"] == "cancel":
                    engine.cancel(command["id"])
                elif command["op"] == "finish":
                    engine.close()

                    def records():
                        return [json.loads(row.split("AIT ", 1)[1])
                                for row in (args.out / "game-stderr.txt").read_text().splitlines()
                                if "AIT {" in row]

                    count = len(records())
                    session._wait(lambda: len(records()) > count, 5,
                                  "post-control independent changed L sample")
                    observation = records()[-1]
                    baseline = records()[0]
                    result = score(observation, baseline)
                    (args.out / "evaluation.json").write_text(json.dumps({
                        "baseline": baseline, "observation": observation, **result},
                        indent=2) + "\n")
                    emit({"event": "independent_evaluation", **result})
                    break
                else:
                    raise ValueError("unsupported command")
            except (ValueError, KeyError, TypeError, Expired) as error:
                emit({"event": "rejected", "reason": str(error)})
    finally:
        if engine:
            engine.close()
        if backend:
            try:
                backend.close()
            finally:
                (args.out / "owner-events.json").write_text(json.dumps(
                    backend.owner.records, indent=2) + "\n")
        if session:
            session.close()
            (args.out / "cleanup.json").write_text(json.dumps({
                "all_owned_processes_exited": all(process.poll() is not None for process in session.procs),
                "save_unchanged": sha(SAVE) == SAVE_SHA}) + "\n")
            shutil.rmtree(session.tmp)


if __name__ == "__main__":
    main()
