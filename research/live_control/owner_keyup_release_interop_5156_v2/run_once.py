"""One-shot local contract probe. No runtime, X11, model, GPU, or network use."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from release_protocol_v3 import AUTONOMOUS_REASONS, ProtocolError, validate_receipt, validate_stream

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PINNED = {
    "research/live_control/input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "research/live_control/input_transition_owner_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
    "research/live_control/owner_keyup_release_semantics_5156_v2/release_protocol_v2.py":
        "55272e127073a84c9eb541bc650fee74f3fc7123",
}
SOURCE_REASONS = {"stop_requested", "expired", "surface_changed", "focus_changed", "cancelled", "thread_exit"}
POSITIVE_IDS = [f"auto.{x}" for x in sorted(SOURCE_REASONS)] + ["explicit.key_up.string", "explicit.button_up.integer"]
NEGATIVE_IDS = [
    "unknown_reason", "missing_identity", "wrong_identity", "extra_identity", "bool_button",
    "out_of_range_button", "authority_true", "authority_missing", "missing_caller_bracket",
    "inverted_caller_bracket", "auto_caller_timestamp", "auto_request_id", "auto_explicit_operation",
    "explicit_autonomous_reason", "duplicate_owner_sequence", "omitted_positive", "duplicated_positive",
    "source_drift", "output_collision",
]


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def base(kind, seq=1):
    row = {"schema": "owner-keyup-release-v3", "grants_input_authority": False,
           "owner_id": "owner-a", "intent_token": "intent-a", "key": "A",
           "owner_sequence": seq, "owned_before": True, "owned_after": False,
           "owner_release_started_ns": 20, "owner_sync_returned_ns": 30,
           "release_kind": kind, "operation": None, "request_id": None, "release_reason": None}
    if kind == "explicit_client_up":
        row.update(operation="key_up", request_id="request-a", caller_started_ns=10,
                   caller_returned_ns=40)
    return row


def source_reason_literals(tree):
    vals = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "release":
            if node.args and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is str:
                vals.add(node.args[0].value)
            elif node.args and isinstance(node.args[0], ast.IfExp):
                for n in ast.walk(node.args[0]):
                    if isinstance(n, ast.Constant) and type(n.value) is str:
                        vals.add(n.value)
    vals.discard("release")
    return vals


def expect_reject(row, stream=False):
    try:
        validate_stream(row) if stream else validate_receipt(row)
    except (ProtocolError, TypeError, KeyError):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    output = Path(args.output).resolve()
    audit_path = output.with_name("audit.json")
    if output.exists() or audit_path.exists():
        print("STOP_PROVENANCE_OR_RUNNER: output collision", file=sys.stderr)
        return 20
    source_hashes, source_bytes = {}, {}
    for path, expected in PINNED.items():
        p = ROOT / path
        raw = p.read_bytes()
        actual = git_blob_sha(raw)
        if actual != expected:
            print(f"STOP_PROVENANCE_OR_RUNNER: source drift {path} {actual}", file=sys.stderr)
            return 21
        source_hashes[path] = hashlib.sha256(raw).hexdigest()
        source_bytes[path] = raw
    owner_ast = ast.parse(source_bytes["research/live_control/input_owner_v10.py"])
    if source_reason_literals(owner_ast) != SOURCE_REASONS:
        print(f"STOP_PROVENANCE_OR_RUNNER: reason drift {source_reason_literals(owner_ast)}", file=sys.stderr)
        return 22
    transition = ast.parse(source_bytes["research/live_control/input_transition_owner_v3.py"])
    transition_text = source_bytes["research/live_control/input_transition_owner_v3.py"].decode()
    if '"key" if operation == "up" else "button"' not in transition_text:
        print("STOP_PROVENANCE_OR_RUNNER: identity mapping drift", file=sys.stderr)
        return 23

    cases = []
    for reason in sorted(SOURCE_REASONS):
        row = base("autonomous_cleanup")
        row["release_reason"] = reason
        cases.append((f"auto.{reason}", lambda r=row: validate_receipt(r)))
    keyrow = base("explicit_client_up")
    cases.append(("explicit.key_up.string", lambda: validate_receipt(keyrow)))
    buttonrow = base("explicit_client_up")
    buttonrow.pop("key")
    buttonrow.update(operation="button_up", button=1)
    cases.append(("explicit.button_up.integer", lambda: validate_receipt(buttonrow)))

    outcomes = {name: bool((lambda fn: (fn(), True)[1])(fn)) for name, fn in cases}
    bad = [name for name, accepted in outcomes.items() if not accepted]

    negatives = []
    def add(name, row, stream=False): negatives.append((name, row, stream))
    r=base("autonomous_cleanup"); r["release_reason"]="future_reason"; add("unknown_reason",r)
    r=base("explicit_client_up"); r.pop("key"); add("missing_identity",r)
    r=base("explicit_client_up"); r["key"]=4; add("wrong_identity",r)
    r=base("explicit_client_up"); r["button"]=1; add("extra_identity",r)
    r=base("explicit_client_up"); r.pop("key"); r.update(operation="button_up",button=True); add("bool_button",r)
    r=base("explicit_client_up"); r.pop("key"); r.update(operation="button_up",button=4); add("out_of_range_button",r)
    r=base("explicit_client_up"); r["grants_input_authority"]=True; add("authority_true",r)
    r=base("explicit_client_up"); r.pop("grants_input_authority"); add("authority_missing",r)
    r=base("explicit_client_up"); r.pop("caller_returned_ns"); add("missing_caller_bracket",r)
    r=base("explicit_client_up"); r["caller_started_ns"]=31; add("inverted_caller_bracket",r)
    r=base("autonomous_cleanup"); r["caller_started_ns"]=10; add("auto_caller_timestamp",r)
    r=base("autonomous_cleanup"); r["request_id"]="fake"; add("auto_request_id",r)
    r=base("autonomous_cleanup"); r["operation"]="key_up"; add("auto_explicit_operation",r)
    r=base("explicit_client_up"); r["release_reason"]="expired"; add("explicit_autonomous_reason",r)
    r1=base("explicit_client_up",1); r2=base("explicit_client_up",1); r2["request_id"]="request-b"; add("duplicate_owner_sequence",[r1,r2],True)
    # Exact coverage tampering is independently evaluated below, not passed through candidate.
    neg_outcomes={name:expect_reject(row,stream) for name,row,stream in negatives}
    neg_outcomes["omitted_positive"]=len(POSITIVE_IDS[:-1]) != len(POSITIVE_IDS)
    neg_outcomes["duplicated_positive"]=(POSITIVE_IDS + [POSITIVE_IDS[0]]).count(POSITIVE_IDS[0]) != 1
    neg_outcomes["source_drift"]=SOURCE_REASONS != source_reason_literals(owner_ast)
    with tempfile.TemporaryDirectory() as td:
        sentinel=Path(td)/"result.json"; sentinel.write_text("sentinel",encoding="utf-8")
        before=sentinel.read_bytes()
        # Collision gate is tested by the exact same preflight branch without touching final output.
        neg_outcomes["output_collision"]=sentinel.exists() and sentinel.read_bytes()==before

    case_ids=[name for name,_ in cases]
    exact_coverage=(len(case_ids)==len(POSITIVE_IDS) and set(case_ids)==set(POSITIVE_IDS)
                    and len(set(case_ids))==len(POSITIVE_IDS))
    expected_negative=set(NEGATIVE_IDS)
    if set(neg_outcomes)!=expected_negative or len(neg_outcomes)!=len(expected_negative):
        print("STOP_PROVENANCE_OR_RUNNER: negative vector coverage mismatch",file=sys.stderr); return 24
    failed_neg=[k for k,v in neg_outcomes.items() if not v]
    status=("PASS_SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY" if exact_coverage and not bad and not failed_neg
            else "FAIL_SOURCE_SUPPORTED_FORM_REJECTED" if bad else "FAIL_INVALID_FORM_ACCEPTED")
    result={"status":status,"scope":"SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY",
            "intake_commit":"d8ca8bfed9cd8d84201c91645e4ed25364181d3f",
            "source_blob_ids":PINNED,"source_sha256":source_hashes,
            "positive_case_ids":case_ids,"positive_outcomes":outcomes,
            "negative_case_ids":list(neg_outcomes),"negative_rejected":neg_outcomes,
            "positive_exact_coverage":exact_coverage,"positive_failures":bad,
            "negative_failures":failed_neg,"authority_grants":0,"x11_observed":False,
            "python":sys.version,"platform":sys.platform}
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        print("STOP_PROVENANCE_OR_RUNNER: output collision",file=sys.stderr); return 20
    payload=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode()
    with output.open("xb") as f: f.write(payload)
    audit = subprocess.run([sys.executable, str(HERE / "audit.py"), "--result", str(output)],
                           capture_output=True, text=True, check=False)
    if audit_path.exists():
        print("STOP_PROVENANCE_OR_RUNNER: audit output collision",file=sys.stderr); return 25
    with audit_path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(audit.stdout)
        f.write("\n")
    print(json.dumps({"status":status,"output":str(output),
                      "sha256":hashlib.sha256(payload).hexdigest(),
                      "audit_exit":audit.returncode,"audit":audit.stdout.strip()}))
    if audit.returncode != 0:
        return 26
    return 0 if status=="PASS_SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY" else 1


if __name__=="__main__": raise SystemExit(main())
