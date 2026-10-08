"""One changed-geometry placement with receipt-dependent target admission."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from mindustry_receipt_session_v1 import Backend, suite
from executor_v8 import Executor
from lease import Expired
from mindustry_single_tile_score_v1 import score

SAVE = HERE / "results/mindustry-reset-01/canonical.msav"
SAVE_SHA = "8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=False)
    assert sha(SAVE) == SAVE_SHA
    sources = [HERE / name for name in ("mindustry_single_tile_interactive_v2.py",
        "mindustry_single_tile_score_v1.py", "mindustry_single_tile_plan_v1.json")]
    sources += sorted((HERE / "mindustry_single_tile_mod_v1").rglob("*"))
    sources += list((HERE.parent / "live_control").glob("*.py"))
    dump(args.out / "manifest.json", {"save_sha256": SAVE_SHA,
        "sources": {str(path.relative_to(HERE.parent)): sha(path) for path in sources if path.is_file()},
        "scope": "one player-built changed-geometry tile; no controller oracle reads",
        "declared_check": json.loads((HERE / "mindustry_single_tile_plan_v1.json").read_text())["task"],
        "gameplay_task_success": None, "model_tokens": None})
    lock = threading.Lock(); session = backend = engine = None
    def emit(record):
        with lock:
            record["emitted_ns"] = time.perf_counter_ns()
            line = json.dumps(record)
            with (args.out / "events.jsonl").open("a") as stream: stream.write(line + "\n")
            print(line, flush=True)
    try:
        with (args.out / "setup.txt").open("w") as setup, contextlib.redirect_stdout(setup):
            session = suite.Session(); root = args.root / "root/usr"; libs = root / "lib/x86_64-linux-gnu"
            session.env.update(LD_LIBRARY_PATH=f"{libs}:{libs}/pulseaudio", LIBGL_ALWAYS_SOFTWARE="1",
                SDL_VIDEODRIVER="x11", SDL_AUDIODRIVER="dummy", ALSOFT_DRIVERS="null")
            session.env.pop("PULSE_SERVER", None); home = Path(session.env["HOME"]); data = home / "mindustry"
            shutil.copytree(HERE / "mindustry_single_tile_mod_v1", data / "mods/interface-single-tile-study")
            shutil.copy2(SAVE, data / "input.msav"); session.env["MINDUSTRY_DATA_DIR"] = str(data)
            jar = args.root / "Mindustry-v160.2-complete.jar"; dump(args.out / "assets.json", {"jar_sha256": sha(jar)})
            with (args.out / "game-stdout.txt").open("w") as stdout, (args.out / "game-stderr.txt").open("w") as stderr:
                session.spawn([str(root / "lib/jvm/java-21-openjdk-amd64/bin/java"), "-Xmx768m",
                    f"-Duser.home={home}", "-jar", str(jar)], cwd=args.out, stdout=stdout, stderr=stderr)
            session._wait(lambda: (data / "ready.txt").exists(), 60, "single-tile fixture ready")
            session.wait_window("Mindustry"); session.focus("Mindustry"); time.sleep(1); backend = Backend(session, args.out, emit)
        engine = Executor(backend, emit)
        plan = json.loads((HERE / "mindustry_single_tile_plan_v1.json").read_text())
        emit({"event": "ready", "task": plan["task"]}); backend.snapshot("initial", 0)
        for line in sys.stdin:
            try:
                command = json.loads(line); emit({"event": "command", "command": command})
                if command["op"] == "submit":
                    engine.submit(command["id"], command["steps"], command["expected_sequence"], command["valid_until_ns"])
                elif command["op"] == "clock":
                    emit({"event": "clock", "runtime_ns": time.perf_counter_ns(), "sequence": backend.sequence})
                elif command["op"] == "cancel": engine.cancel(command["id"])
                elif command["op"] == "finish":
                    engine.close(); (data / "evaluate.txt").write_text("control closed")
                    session._wait(lambda: (data / "evaluated.txt").exists(), 15, "single-tile evaluation")
                    for name in ("before.json", "after.json", "evaluation-error.txt"):
                        if (data / name).exists(): shutil.copy2(data / name, args.out / name)
                    if (args.out / "after.json").exists():
                        value = score(json.loads((args.out / "before.json").read_text()),
                                      json.loads((args.out / "after.json").read_text()), plan)
                    else: value = {"status": "UNKNOWN", "contract_satisfied": None, "reason": "invalid evaluation start"}
                    dump(args.out / "evaluation.json", value); emit({"event": "independent_evaluation", **value}); break
                else: raise ValueError("unsupported command")
            except (ValueError, KeyError, TypeError, Expired) as error: emit({"event": "rejected", "reason": str(error)})
    finally:
        if engine: engine.close()
        if backend:
            try: backend.close()
            finally: dump(args.out / "owner-events.json", backend.owner.records)
        if session:
            session.close(); dump(args.out / "cleanup.json", {"all_owned_processes_exited": all(p.poll() is not None for p in session.procs),
                "save_unchanged": sha(SAVE) == SAVE_SHA}); shutil.rmtree(session.tmp)


if __name__ == "__main__": main()
