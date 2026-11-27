#!/usr/bin/env python3
"""Read-only source identity and narrow static guard-path audit for #59."""
from __future__ import annotations
import argparse, ast, hashlib, json, re, subprocess
from pathlib import Path

CONTROLLER = "research/doom/map01_overlap_controller_v39.py"
SESSION = "research/doom/session_map01_v15.py"
TRIAGE = "research/doom/MAP01_ASTRA_SYSTEM_FAILURE_TRIAGE_V1.md"
GOAL = "docs/CURRENT_GOAL.md"
HISTORICAL = "c1074c4dc385bae5b94ce93a5870e92c2e6ab07d"
EXPECTED_CONTROLLER = "4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca"
EXPECTED_SESSION = "661b3ac311f72517670a8fe37bc2901e9479963af9cdb0a219ed83ea48601724"


def git_show(rev: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], stderr=subprocess.PIPE)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def named(tree: ast.AST, name: str, kinds=(ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
    for node in ast.walk(tree):
        if isinstance(node, kinds) and node.name == name:
            return node
    raise ValueError(f"required AST node absent: {name}")


def call_names(node: ast.AST) -> list[str]:
    out=[]
    for item in ast.walk(node):
        if isinstance(item, ast.Call):
            f=item.func
            if isinstance(f, ast.Attribute):
                out.append(f"{ast.unparse(f.value)}.{f.attr}")
            elif isinstance(f, ast.Name):
                out.append(f.id)
    return out


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--main-sha",required=True)
    args=parser.parse_args()
    current=args.main_sha
    main_controller=git_show(current,CONTROLLER)
    main_session=git_show(current,SESSION)
    current_goal=git_show(current,GOAL).decode()
    triage=git_show(current,TRIAGE).decode()
    old_controller=git_show(HISTORICAL,CONTROLLER)
    old_session=git_show(HISTORICAL,SESSION)
    controller_tree=ast.parse(main_controller)
    session_tree=ast.parse(main_session)
    cover=named(controller_tree,"build_cover_monitor")
    monitor=named(controller_tree,"ObservableSignalPolicyMonitor")
    cancel=named(controller_tree,"cancel_invalidated_cover")
    terminal=named(controller_tree,"require_cover_terminal")
    calls=call_names(cover)
    monitor_text=ast.get_source_segment(main_controller.decode(),monitor) or ""
    goal_claim=re.search(r"Current direction \(r139\):.*?current main `([0-9a-f]{8,40})`",current_goal)
    triage_claim=re.search(r"On current main `([0-9a-f]{40})`",triage)
    triage_hashes={m.group(1):m.group(2) for m in re.finditer(r"(map01_overlap_controller_v39\.py|session_map01_v15\.py).*?SHA-256 `([0-9a-f]{64})`",triage)}
    current_hashes={"controller":sha(main_controller),"session":sha(main_session)}
    expected={"controller":EXPECTED_CONTROLLER,"session":EXPECTED_SESSION}
    result={
      "allocation":"UNJUNO-59-V39-CURRENT-MAIN-SOURCE-IDENTITY-A01-20261009",
      "main_sha":current,
      "r139_current_main_reference":None if goal_claim is None else goal_claim.group(1),
      "triage_current_main_reference":None if triage_claim is None else triage_claim.group(1),
      "current_source_sha256":current_hashes,
      "retained_r139_expected_sha256":expected,
      "triage_recorded_sha256":triage_hashes,
      "historical_c1074_sha256":{"controller":sha(old_controller),"session":sha(old_session)},
      "source_identity_matches_retained":{k:current_hashes[k]==expected[k] for k in expected},
      "historical_controller_equals_retained":sha(old_controller)==EXPECTED_CONTROLLER,
      "historical_session_equals_retained":sha(old_session)==EXPECTED_SESSION,
      "static_guard_path":{
        "build_cover_monitor_lines":[cover.lineno,cover.end_lineno],
        "monitor_class_lines":[monitor.lineno,monitor.end_lineno],
        "monitor_call_names":sorted(set(call_names(monitor))),
        "build_cover_reader_health_call":"reader.read" in calls,
        "build_cover_optional_ammo_call":"ammo_reader.read" in calls,
        "monitor_tracks_frame_hash":"frame_rgb_sha256" in monitor_text,
        "monitor_mentions_enemy_or_threat_classifier":bool(re.search(r"enemy|threat|classifier|pixels",monitor_text,re.I)),
        "cancel_invalidated_cover_lines":[cancel.lineno,cancel.end_lineno],
        "cancel_calls_planner_interrupt":"planner.interrupt" in call_names(cancel),
        "terminal_empty_release_lines":[terminal.lineno,terminal.end_lineno],
        "terminal_checks_verified_release":"verified" in ast.get_source_segment(main_controller.decode(),terminal),
        "terminal_checks_empty_keys":"keys_down" in ast.get_source_segment(main_controller.decode(),terminal),
        "terminal_checks_empty_buttons":"buttons_down" in ast.get_source_segment(main_controller.decode(),terminal),
        "scope_note":"Static inspection of the monitor path only; frame hash equality is identity/integrity evidence, not full-scene threat classification."
      },
      "disposition":"SOURCE_IDENTITY_MATCH" if all(current_hashes[k]==expected[k] for k in expected) else "HOLD_SOURCE_IDENTITY_STALE",
      "live_authorization":"NOT_CHECKED_BY_THIS_SCRIPT; current-main r139 states private game lane unassigned",
      "runtime_invocations":0
    }
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
