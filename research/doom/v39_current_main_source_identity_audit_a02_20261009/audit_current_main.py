#!/usr/bin/env python3
"""Read-only source identity and narrow static guard-path audit for #59."""
from __future__ import annotations
import argparse, ast, hashlib, json, re, subprocess

CONTROLLER = "research/doom/map01_overlap_controller_v39.py"
SESSION = "research/doom/session_map01_v15.py"
MONITOR = "research/live_control/observable_signal_guard_v2.py"
TRIAGE = "research/doom/MAP01_ASTRA_SYSTEM_FAILURE_TRIAGE_V1.md"
GOAL = "docs/CURRENT_GOAL.md"
HISTORICAL = "c1074c4dc385bae5b94ce93a5870e92c2e6ab07d"
EXPECTED = {
    "controller": "4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca",
    "session": "661b3ac311f72517670a8fe37bc2901e9479963af9cdb0a219ed83ea48601724",
}


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
            if isinstance(f, ast.Attribute): out.append(f"{ast.unparse(f.value)}.{f.attr}")
            elif isinstance(f, ast.Name): out.append(f.id)
    return out


def source_segment(raw: bytes, node: ast.AST) -> str:
    return ast.get_source_segment(raw.decode(), node) or ""


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--main-sha",required=True)
    args=parser.parse_args()
    current=args.main_sha
    main_bytes={path:git_show(current,path) for path in (CONTROLLER,SESSION,MONITOR,TRIAGE,GOAL)}
    old_bytes={path:git_show(HISTORICAL,path) for path in (CONTROLLER,SESSION)}
    trees={path:ast.parse(raw) for path,raw in main_bytes.items() if path in (CONTROLLER,SESSION,MONITOR)}
    controller_tree=trees[CONTROLLER]; monitor_tree=trees[MONITOR]
    cover=named(controller_tree,"build_cover_monitor")
    pair=named(controller_tree,"DoomCoverSignalPairMonitor")
    imported_monitor=named(monitor_tree,"ObservableSignalPolicyMonitor")
    cancel=named(controller_tree,"cancel_invalidated_cover")
    terminal=named(controller_tree,"require_cover_terminal")
    cover_calls=call_names(cover); pair_text=source_segment(main_bytes[CONTROLLER],pair)
    monitor_text=source_segment(main_bytes[MONITOR],imported_monitor)
    cancel_calls=call_names(cancel); terminal_text=source_segment(main_bytes[CONTROLLER],terminal)
    current_hashes={"controller":sha(main_bytes[CONTROLLER]),"session":sha(main_bytes[SESSION]),"monitor_helper":sha(main_bytes[MONITOR])}
    old_hashes={"controller":sha(old_bytes[CONTROLLER]),"session":sha(old_bytes[SESSION])}
    goal_claim=re.search(r"Current direction \(r139\):.*?current main `([0-9a-f]{8,40})`",main_bytes[GOAL].decode())
    triage_claim=re.search(r"On current main `([0-9a-f]{40})`",main_bytes[TRIAGE].decode())
    result={
      "allocation":"UNJUNO-59-V39-CURRENT-MAIN-SOURCE-IDENTITY-A02-20261009",
      "main_sha":current,
      "r139_current_main_reference":None if goal_claim is None else goal_claim.group(1),
      "triage_current_main_reference":None if triage_claim is None else triage_claim.group(1),
      "current_source_sha256":current_hashes,
      "retained_r139_expected_sha256":EXPECTED,
      "historical_c1074_sha256":old_hashes,
      "source_identity_matches_retained":{k:current_hashes[k]==EXPECTED[k] for k in EXPECTED},
      "historical_tree_matches_retained":{k:old_hashes[k]==EXPECTED[k] for k in EXPECTED},
      "static_guard_path":{
        "build_cover_monitor_lines":[cover.lineno,cover.end_lineno],
        "signal_pair_monitor_lines":[pair.lineno,pair.end_lineno],
        "monitor_helper_class_lines":[imported_monitor.lineno,imported_monitor.end_lineno],
        "health_signal_reader_called":"reader.read" in cover_calls,
        "optional_ammo_signal_reader_called":"ammo_reader.read" in cover_calls,
        "signal_pair_keys_health_and_ammo":'"health"' in pair_text and '"ammo"' in pair_text,
        "frame_hash_only_coherence_field":"frame_rgb_sha256" in pair_text,
        "monitor_extractor_reads_typed_observation":"self.extractor.read" in call_names(imported_monitor),
        "monitor_classifies_full_scene_threat":bool(re.search(r"enemy|threat.{0,20}(classif|detect)|pixel decoder",monitor_text,re.I)),
        "cancel_invalidated_cover_lines":[cancel.lineno,cancel.end_lineno],
        "cancel_calls_planner_interrupt":"planner.interrupt" in cancel_calls,
        "terminal_empty_release_lines":[terminal.lineno,terminal.end_lineno],
        "terminal_checks_verified_release":"verified" in terminal_text,
        "terminal_checks_empty_keys":"keys_down" in terminal_text,
        "terminal_checks_empty_buttons":"buttons_down" in terminal_text,
        "scope_note":"Static monitor-path facts only. Hash comparison binds frame identity; no live threat classification or timing inference."
      },
      "disposition":"SOURCE_IDENTITY_MATCH" if all(current_hashes[k]==EXPECTED[k] for k in EXPECTED) else "HOLD_SOURCE_IDENTITY_STALE",
      "live_authorization":"NOT_CHECKED_BY_THIS_SCRIPT; current-main r139 states private game lane unassigned",
      "controller_execution_count":0,"session_execution_count":0,"game_gui_model_input_container_invocations":0
    }
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
