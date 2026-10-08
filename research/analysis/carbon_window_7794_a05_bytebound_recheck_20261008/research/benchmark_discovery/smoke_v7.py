#!/usr/bin/env python3
"""Private Linux discovery smoke; no Agent Interface performance claims."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "observation_gating"))
from gui_suite import Session
from PIL import ImageGrab


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def stat(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return {"cpu_s": (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK"),
                "rss_bytes": int(fields[21]) * os.sysconf("SC_PAGE_SIZE")}
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--app", choices=["openttd", "minetest_proxy", "mindustry", "luanti"], required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    r = a.root / "root/usr"
    hashes = {str(p.relative_to(a.root)): {"bytes": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted((a.root / "packages").glob("*.deb"))}
    jar = a.root / "Mindustry-v160.2-complete.jar"
    luanti = a.root / "luanti-5.17.0.deb"
    if luanti.exists():
        hashes[luanti.name] = {"bytes": luanti.stat().st_size, "sha256": hashlib.sha256(luanti.read_bytes()).hexdigest()}
    if jar.exists():
        hashes[jar.name] = {"bytes": jar.stat().st_size,
                            "sha256": hashlib.sha256(jar.read_bytes()).hexdigest()}
    dump(a.out / "manifest.json", {"app": a.app, "assets": hashes,
         "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "plan_sha256": hashlib.sha256((HERE / "plan_v4.json").read_bytes()).hexdigest(),
         "os": Path("/etc/os-release").read_text(), "kernel": os.uname().release,
         "scope": "two fresh launch attempts, not task success or reset reliability estimate"})
    rows = []
    for i in range(2):
        out = a.out / str(i + 1)
        out.mkdir()
        s = Session()
        row = {"attempt": i + 1, "display": s.name, "app": a.app}
        try:
            libs = r / "lib/x86_64-linux-gnu"
            s.env.update(LD_LIBRARY_PATH=f"{libs}:{libs}/pulseaudio",
                         LIBGL_ALWAYS_SOFTWARE="1", SDL_VIDEODRIVER="x11",
                         SDL_AUDIODRIVER="dummy", ALSOFT_DRIVERS="null")
            s.env.pop("PULSE_SERVER", None)
            home = Path(s.env["HOME"])
            if a.app == "openttd":
                data = Path(s.env["XDG_DATA_HOME"]) / "openttd"
                data.mkdir()
                for asset in (r / "share/games/openttd").iterdir():
                    if asset.name != "game":
                        (data / asset.name).symlink_to(asset)
                shutil.copytree(r / "share/games/openttd/game", data / "game")
                shutil.copytree(HERE / "openttd_script_v2", data / "game/interface_feasibility")
                cfg = out / "openttd.cfg"
                cfg.write_text("[game_creation]\nmap_x = 6\nmap_y = 6\ngeneration_seed = 991001\nstarting_year = 1950\n[network]\nserver_advertise = false\n[game_scripts]\nInterfaceFeasibility = \n")
                cmd = [str(r / "games/openttd"), "-c", str(cfg), "-g", "-G", "991001",
                       "-d", "script=4", "-r", "1024x720", "-s", "null", "-m", "null"]
            elif a.app in ("minetest_proxy", "luanti"):
                cfg = out / "minetest.conf"
                cfg.write_text("font_path = /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf\nmono_font_path = /usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf\nfixed_map_seed = 991001\nmg_name = flat\nenable_sound = false\nfps_max = 30\nviewing_range = 40\nscreen_w = 1024\nscreen_h = 720\naddress = 127.0.0.1\nbind_address = 127.0.0.1\nserver_announce = false\n")
                cmd = [str(r / "games/minetest"), "--config", str(cfg), "--world",
                       str(out / "world"), "--gameid", "devtest", "--go", "--name", "feasibility",
                       "--logfile", str(out / "engine.txt")]
                if a.app == "luanti":
                    cmd[0] = str(a.root / "luanti-root/usr/bin/luanti")
                    cmd[cmd.index("--world") + 1] = str(s.tmp / "world")
                    cmd[cmd.index("--gameid") + 1] = "interface_feasibility"
                    games = home / ".minetest/games"
                    games.mkdir(parents=True)
                    shutil.copytree(HERE / "luanti_game_v2", games / "interface_feasibility")
                    cfg.write_text(cfg.read_text().replace("mg_name = flat", "mg_name = singlenode"))
            else:
                data = home / "mindustry"
                mod = data / "mods/interface-feasibility"
                shutil.copytree(HERE / "mindustry_mod_v2", mod)
                s.env["MINDUSTRY_DATA_DIR"] = str(data)
                cmd = [str(r / "lib/jvm/java-21-openjdk-amd64/bin/java"),
                       "-Xmx768m", f"-Duser.home={home}", "-jar", str(jar)]
            row["command"] = cmd
            start = time.monotonic()
            with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
                p = s.spawn(cmd, cwd=out, stdout=stdout, stderr=stderr)
                while time.monotonic() - start < 40 and p.poll() is None:
                    windows = s.windows().strip()
                    if windows:
                        row["window_s"] = time.monotonic() - start
                        break
                    time.sleep(.1)
                row["windows"] = s.windows()
                if row["windows"] and p.poll() is None:
                    time.sleep(8)
                    before = {str(q.pid): stat(q.pid) for q in (p, s.xvfb, s.openbox)}
                    t = time.monotonic()
                    samples = []
                    for _ in range(10):
                        samples.append({str(q.pid): stat(q.pid) for q in (p, s.xvfb, s.openbox)})
                        time.sleep(.5)
                    after = {str(q.pid): stat(q.pid) for q in (p, s.xvfb, s.openbox)}
                    row["sample_seconds"] = time.monotonic() - t
                    row["resources"] = {"before": before, "after": after, "samples": samples,
                                        "roles": {"app": p.pid, "xvfb": s.xvfb.pid, "wm": s.openbox.pid}}
                    img = ImageGrab.grab(xdisplay=s.name)
                    img.save(out / "screen.png")
                    row["screen_sha256"] = hashlib.sha256((out / "screen.png").read_bytes()).hexdigest()
                row["pre_cleanup_returncode"] = p.poll()
                if p.poll() is None:
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(timeout=10)
                        row["forced_kill"] = False
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=5)
                        row["forced_kill"] = True
                row["returncode"] = p.returncode
                row["total_s"] = time.monotonic() - start
            if a.app == "luanti" and (s.tmp / "world").exists():
                shutil.copytree(s.tmp / "world", out / "world")
            if a.app == "mindustry":
                for f in (home / "mindustry").glob("oracle-*.json"):
                    shutil.copy2(f, out / f.name)
            # Preserve configuration/state listings before disposal, without large caches.
            row["home_files"] = [str(p.relative_to(home)) for p in home.rglob("*") if p.is_file()]
        except Exception as e:
            row["error"] = repr(e)
        finally:
            s.close()
            for p in s.procs:
                p.wait(timeout=5)
            row["all_owned_processes_exited"] = all(p.poll() is not None for p in s.procs)
            shutil.rmtree(s.tmp)
            dump(out / "result.json", row)
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k not in ("resources", "home_files")}), flush=True)
    dump(a.out / "results.json", rows)


if __name__ == "__main__":
    main()
