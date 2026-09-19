import json, os, shutil, signal, subprocess, tempfile, time
from pathlib import Path

COMMANDS = {
    "Xvfb": ["Xvfb", ":151", "-screen", "0", "1600x1000x24"],
    "inkscape": ["inkscape"],
    "libreoffice": ["libreoffice", "--norestore", "--nolockcheck", "--calc"],
    "chromium": ["chromium", "--no-sandbox", "--disable-gpu", "about:blank"],
    "xdotool": ["xdotool", "search", "--onlyvisible", "--name", ".*"],
}

def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-2821-diagnostic-"))
    env = os.environ.copy()
    env.update(DISPLAY=":151", XAUTHORITY=str(root / "Xauthority"), HOME=str(root / "home"),
               XDG_CONFIG_HOME=str(root / "config"), XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"), GDK_BACKEND="x11", SAL_USE_VCLPLUGIN="gen")
    for name in ("home", "config", "cache", "runtime"):
        (root / name).mkdir(mode=0o700)
    (root / "Xauthority").touch(mode=0o600)
    out = {"decision": "HOLD_MIXED_APP_STARTUP_DIAGNOSTIC", "display": env["DISPLAY"],
           "commands": {}, "launches": [], "input_operations": 0, "model_calls": 0,
           "network_calls": 0}
    for name, argv in COMMANDS.items():
        out["commands"][name] = {"argv": argv, "which": shutil.which(argv[0])}
    xvfb = None
    try:
        xvfb = subprocess.Popen(COMMANDS["Xvfb"] + ["-auth", str(root / "Xauthority")], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        time.sleep(1)
        out["xvfb_alive"] = xvfb.poll() is None
        for name in ("inkscape", "libreoffice", "chromium"):
            argv = COMMANDS[name]
            try:
                p = subprocess.Popen(argv, env=env, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.PIPE, text=True)
                time.sleep(1)
                out["launches"].append({"name": name, "pid": p.pid, "alive": p.poll() is None,
                                        "stderr": (p.stderr.read(200) if p.poll() is not None else "")})
                if p.poll() is None:
                    p.terminate()
            except Exception as exc:
                out["launches"].append({"name": name, "error": repr(exc)})
        out["decision"] = "PASS_MIXED_APP_STARTUP_DIAGNOSTIC" if out["xvfb_alive"] and all(x.get("which") for x in out["commands"].values()) and all("error" not in x for x in out["launches"]) else "STOP_MIXED_APP_STARTUP_DIAGNOSTIC"
    except Exception as exc:
        out["decision"] = "STOP_MIXED_APP_STARTUP_DIAGNOSTIC"
        out["error"] = repr(exc)
    finally:
        if xvfb is not None and xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if out["decision"].startswith("PASS") else 1)

if __name__ == "__main__": main()