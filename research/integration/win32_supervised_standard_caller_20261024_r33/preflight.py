"""Input-free R33 custody, source and recovery-trace instrumentation preflight."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import winreg
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
C = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
OUT = {"schema": "win32-supervised-standard-caller-r33-preflight-v1",
       "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "native_input_sent": False, "checks": {}}

try:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                     text=True).strip()
    OUT["source_commit"] = commit
    OUT["conditions_sha256"] = hashlib.sha256(
        (PACKET / "conditions.json").read_bytes()).hexdigest()
    OUT["checks"]["frozen_commit_and_conditions_hash"] = (
        commit == C["source_commit"])
    tracked = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"],
                             cwd=ROOT).returncode == 0
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"],
                            cwd=ROOT).returncode == 0
    OUT["checks"]["tracked_tree_clean"] = tracked and staged

    source_hashes = {}
    for rel in C["source_sha256"]:
        path = PACKET / rel if rel in C["packet_source_files"] else ROOT / rel
        source_hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    OUT["source_sha256"] = source_hashes
    OUT["checks"]["source_hashes_match"] = source_hashes == C["source_sha256"]
    frozen = {rel: hashlib.sha256((PACKET / rel).read_bytes()).hexdigest()
              for rel in C["frozen_files"]}
    OUT["frozen_packet_hashes"] = frozen
    OUT["checks"]["frozen_packet_hashes_match"] = frozen == C["frozen_files"]
    predecessor = C["predecessor"]
    pred_raw_path = ROOT / predecessor["raw_path"]
    pred_audit_path = ROOT / predecessor["audit_path"]
    pred_diag_path = ROOT / predecessor["trace_diagnosis_path"]
    pred_hashes = {"raw": hashlib.sha256(pred_raw_path.read_bytes()).hexdigest(),
                   "audit": hashlib.sha256(pred_audit_path.read_bytes()).hexdigest(),
                   "trace_diagnosis": hashlib.sha256(pred_diag_path.read_bytes()).hexdigest()}
    pred_raw = json.loads(pred_raw_path.read_text(encoding="utf-8"))
    pred_audit = json.loads(pred_audit_path.read_text(encoding="utf-8"))
    pred_diag = json.loads(pred_diag_path.read_text(encoding="utf-8"))
    OUT["predecessor_hashes"] = pred_hashes
    OUT["checks"]["predecessor_hashes_match"] = pred_hashes == {
        "raw": predecessor["raw_sha256"],
        "audit": predecessor["audit_sha256"],
        "trace_diagnosis": predecessor["trace_diagnosis_sha256"]}
    polls = pred_raw.get("post_cancel_io_hold", {}).get("status_polls", [])
    q_up_spans = pred_diag.get("exact_q_up_sendinput_spans", [])
    q_up_returned_before_callback = any(
        row.get("helper_role") == "recovery"
        and row.get("fields", {}).get("vk") == ord("Q")
        and row.get("fields", {}).get("key_up") is True
        and type(row.get("end_ns")) is int
        and row["end_ns"] < pred_diag.get("callback_return_ns", 0)
        for row in q_up_spans)
    OUT["predecessor_semantics"] = {
        "strict_17_of_20": pred_audit.get("status") == "FAIL_OR_UNKNOWN"
            and pred_audit.get("passed") == 17 and pred_audit.get("total") == 20,
        "r32_did_not_capture_pre_cancel_down_baseline":
            "pre_cancel_independent_readback" not in pred_raw,
        "callback_after_hold": pred_raw.get("hook_stopped", {}).get(
            "callback_return_ns", 0) > pred_raw.get("post_cancel_io_hold", {}).get(
                "ended_monotonic_ns", 0),
        "recovery_q_up_sendinput_returned_before_callback_release":
            q_up_returned_before_callback,
        "independent_effect_and_cleanup": pred_raw.get("independent_readback", {}).get(
            "q_down") is False and pred_raw.get("fixture", {}).get("exit_code") == 0}
    OUT["checks"]["predecessor_semantics_match"] = all(
        OUT["predecessor_semantics"].values())
    trial = C["trial"]
    declared_text = trial.get("text_effect", "")
    text_operations = [op.get("text") for op in trial.get("operations", [])
                       if op.get("op") == "text"]
    OUT["task_effect_oracle"] = {"declared_text": declared_text,
        "text_operations": text_operations,
        "expected_effect": trial.get("expected_effect")}
    OUT["checks"]["task_effect_oracle_matches_frozen_operations"] = (
        trial.get("expected_effect", {}).get("text") == declared_text
        and text_operations == ([declared_text] if declared_text else [])
        and trial.get("expected_effect", {}).get("clicked") is True
        and trial.get("expected_effect", {}).get("saved") is True)

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
        try:
            value, typ = winreg.QueryValueEx(key, "LowLevelHooksTimeout")
            registry = {"present": True, "value": value, "type": typ}
        except FileNotFoundError:
            registry = {"present": False, "value": None, "type": None}
    OUT["registry_read_only"] = registry
    OUT["checks"]["registry_value_unchanged_absent"] = not registry["present"]

    env = os.environ.copy()
    trace_path = PACKET / "instrumentation_preflight.jsonl"
    env["AGENT_INTERFACE_CANCEL_TRACE"] = str(trace_path)
    env["AGENT_INTERFACE_REPO_ROOT"] = str(ROOT)
    env["PYTHONPATH"] = str(PACKET / "instrumentation") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    smoke = r'''
import json, time, types
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
from runtime.cli_v1 import win32_supervisor_helpers as helpers
from runtime.backends.win32_v1 import backend as bm
assert OperationCancellationSupervisor._exchange_helper.__name__ == "traced_exchange"
assert helpers._recover.__name__ == "traced_recover"
assert helpers._helper_main.__name__ == "traced_helper_main"
assert bm.Win32Backend.release_all.__name__ == "traced_release_all"
assert bm.Win32Backend._send.__name__ == "traced_send"
class Proc:
    pid=999001
    def is_alive(self): return True
class Conn:
    def __init__(self): self.rows=[{"x":1},{"control":"operation_complete","request_id":"smoke"}]
    def send(self, value): pass
    def poll(self, timeout): return bool(self.rows)
    def recv(self): return self.rows.pop(0)
obj=object.__new__(OperationCancellationSupervisor)
obj._helpers={"recovery":{"process":Proc(),"connection":Conn(),"identity":{"pid":999001,"creation_time_100ns":1},"available":True,"lock":__import__("threading").Lock()}}
obj._process_identity_reader=lambda p:{"pid":p.pid,"creation_time_100ns":1}
obj._clock_ns=time.monotonic_ns
obj._bounded_wait=lambda deadline,cap:min(cap,max(0,(deadline-time.monotonic_ns())/1e9))
obj._terminate_grace_s=.01; obj._kill_grace_s=.01; obj._poll_interval_s=.001
assert obj._exchange_helper("recovery",{"request_id":"smoke","recovery_id":"smoke"},time.monotonic_ns()+1_000_000_000)=={"x":1}
class FakeUser32:
    def SendInput(self,*args): return 1
fake=object.__new__(bm.Win32Backend)
fake.user32=FakeUser32(); fake.emissions=0; fake.held_keys={}; fake.held_key_targets={}
fake.held_buttons=set(); fake.held_button_targets={}; fake.pending_unicode_ups=set(); fake._last_state_query_witness=[]
fake.target_generation=lambda target:"generation-smoke"
fake.close=lambda:None
fake._key_down_state=lambda vk,target:False
from types import MethodType
def send_key(self,vk,down):
    item=bm.INPUT(type=bm.INPUT_KEYBOARD)
    item.ki=bm.KEYBDINPUT(vk,0,0 if down else bm.KEYEVENTF_KEYUP,0,0)
    bm.Win32Backend._send(self,item)
fake._send_key=MethodType(send_key,fake)
def factory(targets): return fake
request={"operation_id":"op","target_generation":"generation-smoke","recovery_id":"rec","deadline_ns":time.monotonic_ns()+2_000_000_000,"obligations":["key:fixture:Q"]}
receipt=helpers._recover(request,backend_factory=factory,configured_targets={"fixture":1})
assert receipt["release_accepted"] is True and fake.emissions==1
print("R33_TRACE_SELFTEST_PASS")
'''
    run = subprocess.run([sys.executable, "-c", smoke], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=15)
    events = ([json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
              if trace_path.exists() else [])
    OUT["instrumentation_smoke"] = {"returncode": run.returncode,
        "stdout": run.stdout, "stderr": run.stderr, "trace_events": events}
    expected = {"exchange_enter", "exchange_return", "recover_enter", "recover_return",
                "release_all_enter", "release_all_return", "sendinput_enter", "sendinput_return"}
    seen = {row.get("event") for row in events}
    OUT["checks"]["trace_wrappers_fake_selftest"] = (
        run.returncode == 0 and "R33_TRACE_SELFTEST_PASS" in run.stdout
        and expected <= seen
        and any(row.get("key_up") is True and row.get("vk") == ord("Q")
                for row in events if row.get("event") == "sendinput_return"))
    OUT["platform"] = platform.platform()
    OUT["python"] = sys.version
    OUT["checks"]["native_windows"] = sys.platform == "win32"
    OUT["status"] = "PASS" if all(OUT["checks"].values()) else "FAIL_OR_UNKNOWN"
except BaseException as error:
    OUT["status"] = "FAIL_OR_UNKNOWN"
    OUT["error"] = {"type": type(error).__name__, "detail": str(error)}

(PACKET / "preflight.json").write_text(json.dumps(OUT, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
print(json.dumps({"status": OUT["status"], "checks": OUT["checks"],
                  "native_input_sent": False}, sort_keys=True))
raise SystemExit(0 if OUT["status"] == "PASS" else 1)
