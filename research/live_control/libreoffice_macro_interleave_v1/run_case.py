#!/usr/bin/env /usr/bin/python3
import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point, Size


def prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def connect(port, timeout_s=8.0):
    ctx = uno.getComponentContext()
    resolver = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        try:
            return resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
        except Exception as exc:
            last = exc
            time.sleep(0.05)
    raise RuntimeError(f"UNO connect timeout: {last}")


def x(shape):
    return int(shape.getPosition().X)


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wait_for(path, timeout_s):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return time.monotonic_ns()
        time.sleep(0.001)
    raise RuntimeError(f"timeout waiting for {path.name}")


def parse_stdout(cp_or_proc_output):
    return json.loads(cp_or_proc_output.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["window_stable", "window_concurrent"], required=True)
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--macro-source", required=True)
    ap.add_argument("--writer", required=True)
    ap.add_argument("--invoker", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    barrier = out / "validation_barrier.json"
    ready = out / "writer_ready.json"
    go = out / "writer_go"
    profile = Path(tempfile.mkdtemp(prefix=f"lo-interleave-{args.case_id}-"))
    macro_dir = profile / "user" / "Scripts" / "python"
    macro_dir.mkdir(parents=True)
    shutil.copyfile(args.macro_source, macro_dir / "conditional_window_macro.py")

    port = free_port()
    office_cmd = [
        "soffice", "--headless", "--nologo", "--nodefault", "--nofirststartwizard",
        f"-env:UserInstallation=file://{profile}",
        f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
    ]
    office_env = os.environ.copy()
    office_env["PYTHONPATH"] = "/usr/lib/python3/dist-packages"
    office = subprocess.Popen(office_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=office_env)

    result = {"case_id": args.case_id, "scenario": args.scenario, "port": port}
    events = []
    doc = desktop = None
    writer_proc = macro_proc = None
    try:
        remote = connect(port)
        smgr = remote.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", remote)
        doc = desktop.loadComponentFromURL("private:factory/sdraw", "_blank", 0, (prop("Hidden", True),))
        page = doc.getDrawPages().getByIndex(0)
        A = doc.createInstance("com.sun.star.drawing.RectangleShape")
        A.Name = "A"
        A.setPosition(Point(1000, 1000))
        A.setSize(Size(1000, 1000))
        page.add(A)
        B = doc.createInstance("com.sun.star.drawing.RectangleShape")
        B.Name = "B"
        B.setPosition(Point(5000, 1000))
        B.setSize(Size(1000, 1000))
        page.add(B)
        events.append({"event": "fixture_ready", "t_ns": time.monotonic_ns(), "a_x": x(A), "b_x": x(B)})

        writer = None
        if args.scenario == "window_concurrent":
            writer_proc = subprocess.Popen(
                ["/usr/bin/python3", args.writer, str(port), str(ready), str(go), "1700"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            ready_seen_ns = wait_for(ready, 5.0)
            ready_payload = json.loads(ready.read_text(encoding="utf-8"))
            events.append({"event": "writer_ready", "t_ns": ready_seen_ns, "writer_ready_ns": ready_payload["ready_ns"]})

        macro_proc = subprocess.Popen(
            ["/usr/bin/python3", args.invoker, str(port), str(barrier), "500"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        barrier_seen_ns = wait_for(barrier, 5.0)
        barrier_payload = json.loads(barrier.read_text(encoding="utf-8"))
        events.append({
            "event": "validation_barrier_seen",
            "t_ns": barrier_seen_ns,
            "validation_ns": barrier_payload["validation_ns"],
            "before_x": barrier_payload["before_x"],
        })

        if args.scenario == "window_concurrent":
            go_write_ns = time.monotonic_ns()
            go.write_text("go\n", encoding="utf-8")
            events.append({"event": "writer_go", "t_ns": go_write_ns})
            writer_stdout, writer_stderr = writer_proc.communicate(timeout=5)
            writer = parse_stdout(writer_stdout)
            writer["stderr"] = writer_stderr
            events.append({
                "event": "writer_complete",
                "t_ns": time.monotonic_ns(),
                "set_call_start_ns": writer["set_call_start_ns"],
                "set_call_end_ns": writer["set_call_end_ns"],
                "after_x": writer["after_x"],
            })

        macro_stdout, macro_stderr = macro_proc.communicate(timeout=5)
        macro = parse_stdout(macro_stdout)
        macro["stderr"] = macro_stderr
        events.append({"event": "macro_complete", "t_ns": time.monotonic_ns(), "macro": macro})

        result.update({
            "barrier": barrier_payload,
            "barrier_seen_ns": barrier_seen_ns,
            "writer": writer,
            "macro": macro,
            "final_a_x": x(A),
            "final_b_x": x(B),
        })
        m = macro["macro"]
        stable_ok = (
            m.get("status") == "APPLIED" and m.get("before_x") == 1000 and
            m.get("prewrite_x") == 1000 and m.get("after_x") == 1200 and
            result["final_a_x"] == 1200 and result["final_b_x"] == 5000
        )
        if args.scenario == "window_stable":
            ok = stable_ok
        else:
            ok = (
                m.get("status") == "APPLIED" and m.get("before_x") == 1000 and
                writer is not None and writer.get("ok") is True and
                writer.get("before_x") == 1000 and writer.get("after_x") == 1700 and
                m.get("validation_ns") < writer.get("set_call_start_ns") < writer.get("set_call_end_ns") < m.get("prewrite_ns") < m.get("set_start_ns") <= m.get("set_end_ns") < macro.get("invoke_end_ns") and
                m.get("prewrite_x") == 1700 and m.get("after_x") == 1200 and
                result["final_a_x"] == 1200 and result["final_b_x"] == 5000
            )
        result["case_gate_pass"] = bool(ok)
        write_json(out / "events.json", events)
        write_json(out / "result.json", result)
        return 0 if ok else 3
    except Exception as exc:
        result["exception"] = f"{type(exc).__name__}:{exc}"
        write_json(out / "events.json", events)
        write_json(out / "result.json", result)
        return 4
    finally:
        for child in (writer_proc, macro_proc):
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=1)
                except Exception:
                    child.kill()
        try:
            if doc is not None:
                doc.close(True)
        except Exception:
            try:
                doc.dispose()
            except Exception:
                pass
        try:
            if desktop is not None:
                desktop.terminate()
        except Exception:
            pass
        try:
            office.wait(timeout=3)
        except Exception:
            office.terminate()
            try:
                office.wait(timeout=2)
            except Exception:
                office.kill()
                office.wait()
        stdout, stderr = office.communicate() if office.stdout else ("", "")
        (out / "soffice_stdout.txt").write_text(stdout or "", encoding="utf-8")
        (out / "soffice_stderr.txt").write_text(stderr or "", encoding="utf-8")

if __name__ == "__main__":
    raise SystemExit(main())
