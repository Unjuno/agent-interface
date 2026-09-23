import os
import subprocess
import sys
import time

sys.path.insert(0, "/harness")
import runner


def launch_ready(label, title, port):
    page = (
        "data:text/html,<body><script>document.title='READY-" + title +
        "';document.onkeydown=e=>{if(e.key==='Enter'){document.title='" + title +
        "-EFFECT';document.body.dataset.effect='" + title + "'}}</script></body>"
    )
    return runner.start([
        "/usr/bin/chromium", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", f"--user-data-dir=/tmp/obstac-{label}",
        f"--remote-debugging-port={port}", "--no-first-run", "--app=" + page,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_ready(title):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        marker = "READY-" + title
        r = subprocess.run(["xdotool", "search", "--name", "^" + marker + "$"],
                           text=True, capture_output=True)
        if r.returncode == 0 and r.stdout.strip():
            wid = int(r.stdout.splitlines()[0])
            exact = subprocess.run(["xdotool", "getwindowname", str(wid)],
                                   text=True, capture_output=True)
            if exact.returncode == 0 and exact.stdout.strip() == marker:
                return wid
        time.sleep(0.1)
    raise TimeoutError("script readiness marker absent: " + title)


def main():
    os.environ["DISPLAY"] = ":156"
    xv = runner.start(["Xvfb", ":156", "-screen", "0", "1024x768x24", "-ac"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.4)
    try:
        launch_ready("probe-p2", "PROBE-P2", 9612)
        launch_ready("probe-decoy", "PROBE-DECOY", 9613)
        p2w = wait_ready("PROBE-P2")
        decoyw = wait_ready("PROBE-DECOY")
        observations = []
        for wid, title in ((p2w, "PROBE-P2"), (decoyw, "PROBE-DECOY")):
            focus = subprocess.run(["xdotool", "windowfocus", "--sync", str(wid)],
                                   text=True, capture_output=True)
            focused = subprocess.run(["xdotool", "getwindowfocus"],
                                     text=True, capture_output=True)
            send = subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"],
                                  text=True, capture_output=True)
            time.sleep(0.4)
            effect = subprocess.run(["xdotool", "search", "--name", title + "-EFFECT"],
                                    text=True, capture_output=True).returncode == 0
            observations.append({
                "title": title, "window": wid,
                "focus_rc": focus.returncode,
                "focus_id": focused.stdout.strip(), "send_rc": send.returncode,
                "effect": effect,
            })
        print(observations)
    finally:
        for p in reversed(runner.PROCESSES):
            runner.stop(p)


if __name__ == "__main__":
    main()
