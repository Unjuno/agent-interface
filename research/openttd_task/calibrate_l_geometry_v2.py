"""Create a model-free five-tile L fixture for an explicit OpenTTD seed.

This calibration runner never changes the retained seed-991003 fixture.  It
records the derived geometry, byte-pinned save and two observer-only restores
so a candidate seed can be selected before a planner allocation is frozen.
"""
import argparse
import hashlib
import json
import os
import shutil
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "observation_gating"))
from gui_suite import Session, base
from PIL import ImageGrab


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    return [
        json.loads(line.split("AIT ", 1)[1])
        for line in path.read_text().splitlines()
        if "AIT {" in line
    ]


def run_phase(root, out, saved, seed, phase):
    destination = out / phase
    destination.mkdir()
    session = Session()
    row = {"phase": phase, "seed": seed}
    runtime = root / "root/usr"
    try:
        libraries = runtime / "lib/x86_64-linux-gnu"
        session.env.update(
            LD_LIBRARY_PATH=f"{libraries}:{libraries}/pulseaudio",
            SDL_VIDEODRIVER="x11",
            SDL_AUDIODRIVER="dummy",
            LIBGL_ALWAYS_SOFTWARE="1",
        )
        data = Path(session.env["XDG_DATA_HOME"]) / "openttd"
        data.mkdir()
        for source in (runtime / "share/games/openttd").iterdir():
            if source.name != "game":
                (data / source.name).symlink_to(source)
        shutil.copytree(runtime / "share/games/openttd/game", data / "game")
        script = "setup_l_v1" if phase == "setup" else "observer_l_v1"
        shutil.copytree(HERE / script, data / "game/interface_task")
        config = destination / "openttd.cfg"
        config.write_text(
            "[game_creation]\nmap_x = 6\nmap_y = 6\nstarting_year = 1950\n"
            "[game_scripts]\nInterfaceTask = \n"
        )
        command = [
            str(runtime / "games/openttd"),
            "-c", str(config), "-d", "script=4", "-s", "null", "-m", "null",
            "-r", "1024x720", "-g",
        ]
        command += [str(saved)] if phase.startswith("restore") else ["-G", str(seed)]
        row["command"] = command
        if saved.exists():
            row["save_before"] = sha(saved)
        with (destination / "stdout.txt").open("w") as stdout, (destination / "stderr.txt").open("w") as stderr:
            process = session.spawn(command, cwd=destination, stdout=stdout, stderr=stderr)
            deadline = time.monotonic() + 40
            while process.poll() is None and time.monotonic() < deadline:
                log = (destination / "stderr.txt").read_text()
                if any(token in log for token in ("AIT_READY", "AIT_ERROR", "script died unexpectedly")):
                    break
                time.sleep(0.1)
            row["ready"] = "AIT_READY" in (destination / "stderr.txt").read_text()
            if phase == "setup" and row["ready"]:
                session.focus("OpenTTD")
                driver = base.Driver(session, settle_ms=20)
                base.CHAR_GAP_MS = 12
                driver.key("grave")
                time.sleep(0.2)
                observation = records(destination / "stderr.txt")[0]
                x, y, width = observation["x"], observation["y"], observation["width"]
                target = [y * width + x, y * width + x + 1, y * width + x + 2,
                          (y + 1) * width + x + 2, (y + 2) * width + x + 2]
                row["target_contract"] = {"x": x, "y": y, "width": width, "target": target}
                row["setup_scroll_command"] = f"scrollto {(y + 4) * width + x + 6}"
                driver.text(row["setup_scroll_command"])
                driver.key("Return")
                time.sleep(0.3)
                temporary = session.tmp / "baseline.sav"
                row["setup_console_command"] = f"save {temporary.with_suffix('')}"
                driver.text(row["setup_console_command"])
                driver.key("Return")
                deadline = time.monotonic() + 15
                last_size = None
                stable = 0
                while time.monotonic() < deadline:
                    if temporary.exists():
                        size = temporary.stat().st_size
                        stable = stable + 1 if size == last_size and size > 0 else 0
                        last_size = size
                        if stable >= 3:
                            break
                    time.sleep(0.2)
                if not temporary.exists() or stable < 3:
                    raise RuntimeError("save not completed")
                shutil.copy2(temporary, saved)
                row["save_created"] = sha(saved)
                driver.key("grave")
            time.sleep(0.4)
            ImageGrab.grab(xdisplay=session.name).save(destination / "screen.png")
            row["screen_sha256"] = sha(destination / "screen.png")
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except Exception:
                    os.killpg(process.pid, signal.SIGKILL)
        if saved.exists():
            row["save_after"] = sha(saved)
    except Exception as error:
        row["error"] = repr(error)
        ImageGrab.grab(xdisplay=session.name).save(destination / "error-screen.png")
    finally:
        session.close()
        for process in session.procs:
            process.wait(timeout=5)
        row["all_owned_processes_exited"] = all(process.poll() is not None for process in session.procs)
        shutil.rmtree(session.tmp)
        (destination / "result.json").write_text(json.dumps(row, indent=2) + "\n")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    args.root = args.root.resolve()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    sources = [
        Path(__file__).resolve(), HERE / "audit_l_geometry_v2.py",
        HERE / "guarded_l_score_v1.py",
        *sorted((HERE / "setup_l_v1").glob("*")),
        *sorted((HERE / "observer_l_v1").glob("*")),
        HERE / "results/l-geometry-01/audit.json",
        HERE / "results/l-geometry-01/baseline.sav",
        HERE.parent / "observation_gating/gui_suite.py",
        HERE.parent / "real_apps_v1/real_app_suite_v1.py",
    ]
    manifest = {
        "scope": "model-free candidate L geometry calibration; no planner or task input after save",
        "seed": args.seed,
        "sources": {path.relative_to(HERE.parent).as_posix(): sha(path) for path in sources},
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    saved = args.out / "baseline.sav"
    results = [run_phase(args.root, args.out, saved, args.seed, "setup")]
    if saved.exists():
        results.extend(
            run_phase(args.root, args.out, saved, args.seed, phase)
            for phase in ("restore-1", "restore-2")
        )
    summary = {
        "seed": args.seed,
        "save_sha256": sha(saved) if saved.exists() else None,
        "target_contract": results[0].get("target_contract"),
        "phases_run": [row["phase"] for row in results],
        "ready": [row.get("ready", False) for row in results],
        "all_owned_processes_exited": all(row["all_owned_processes_exited"] for row in results),
        "errors": [row.get("error") for row in results if "error" in row],
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
