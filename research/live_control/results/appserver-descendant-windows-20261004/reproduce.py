import datetime, importlib.util, json, os, pathlib, signal, subprocess, sys, time

root = pathlib.Path(__file__).resolve().parent
module_path = root / "codex_app_server_client_v2.py"
spec = importlib.util.spec_from_file_location("client_under_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CodexAppServerClient = module.CodexAppServerClient
result = {
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "python": sys.version,
    "platform": sys.platform,
    "source": str(module_path),
    "source_sha256": __import__("hashlib").sha256(module_path.read_bytes()).hexdigest(),
    "timeout_seconds": 0.2,
    "steps": [],
}
client = None
child_pid = None
try:
    child_code = (
        "import json,subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        "print(json.dumps({'method':'started','params':{'descendant_pid':p.pid}}),flush=True); "
        "time.sleep(30)"
    )
    client = CodexAppServerClient([sys.executable, "-c", child_code])
    started = client.wait_notification(lambda row: row.get("method") == "started", timeout=5)
    child_pid = started["params"]["descendant_pid"]
    result["descendant_pid"] = child_pid
    result["steps"].append({"step": "spawn", "outcome": "direct client child emitted start; grandchild pid received over actual client stdout"})

    try:
        client.close(timeout=0.2)
        result["close_outcome"] = "returned"
    except BaseException as exc:
        result["close_outcome"] = type(exc).__name__ + ": " + str(exc)

    time.sleep(0.1)
    try:
        os.kill(child_pid, 0)
        alive = True
    except OSError:
        alive = False
    result["descendant_alive_after_close"] = alive
    result["reader_alive_after_close"] = client._reader.is_alive()
    result["stdout_open_after_close"] = not client.process.stdout.closed
    result["steps"].append({
        "step": "bounded_close", "outcome": result["close_outcome"],
        "descendant_alive": alive, "reader_alive": result["reader_alive_after_close"],
        "stdout_open": result["stdout_open_after_close"],
    })
    result["reproduced"] = (
        result["close_outcome"].startswith("TimeoutError:") and alive and
        result["reader_alive_after_close"] and result["stdout_open_after_close"]
    )
finally:
    if child_pid is not None:
        try:
            os.kill(child_pid, signal.SIGTERM)
            result["cleanup_signal"] = "os.kill(SIGTERM)"
        except OSError as exc:
            result["cleanup_signal"] = "already absent: " + repr(exc)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
                time.sleep(0.02)
            except OSError:
                break
    if client is not None:
        client._reader.join(timeout=3)
        result["reader_dead_after_cleanup"] = not client._reader.is_alive()
        for name in ("stdin", "stdout", "stderr"):
            stream = getattr(client.process, name, None)
            if stream is not None and not stream.closed:
                stream.close()
        result["direct_child_returncode"] = client.process.poll()
    result["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

(root / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
if not result.get("reproduced") or not result.get("reader_dead_after_cleanup"):
    raise SystemExit(1)
