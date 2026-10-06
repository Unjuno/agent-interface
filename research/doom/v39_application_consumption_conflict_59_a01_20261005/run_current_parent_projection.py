#!/usr/bin/env python3
"""Replay the projection-focused tests after syncing to current #7602."""
import ast
import hashlib
import io
import json
import subprocess
import sys
import unittest
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
REPO = ROOT.parents[2]
SOURCE = DOOM / "map01_overlap_controller_v39.py"
TEST_SOURCE = DOOM / "test_map01_v39_typed_state_feedback.py"
NAMES = {
    "test_input_edge_receipt_projects_retained_a01_adapter_edges_separately",
    "test_input_edge_receipt_pairs_retained_absolute_pair_release_trace",
    "test_retained_v39_trace_with_unscoped_admissions_stays_unpaired",
    "test_input_edge_receipt_rejects_adapter_actuation_identity_mismatch",
    "test_adapter_edges_must_match_owner_generated_brackets",
    "test_adapter_event_kind_must_match_nested_edge",
    "test_measurement_edge_discriminator_must_match_outer_and_nested_edge",
    "test_application_consumption_claim_must_not_contradict_adapter_projection",
    "test_adapter_pair_requires_consistent_samples_and_request_timing",
    "test_adapter_edge_pairs_reject_interval_conflicting_with_owner_bracket",
    "test_adapter_edge_pairs_require_strictly_separated_down_and_up_intervals",
    "test_input_edge_receipt_pairs_per_key_admission_and_server_keyup_without_secrets",
    "test_input_edge_receipt_keeps_missing_release_unpaired",
    "test_input_edge_receipt_does_not_join_different_intent_tokens",
    "test_input_edge_receipt_does_not_derive_interval_outside_release_bracket",
    "test_input_edge_receipt_allows_owner_lock_wait_after_release_wrapper_starts",
    "test_input_edge_receipt_rejects_release_wrapper_before_input_ack",
    "test_input_edge_receipt_requires_all_sync_and_owner_history_confirmations",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(revision):
    try:
        return subprocess.check_output(
            ["git", "rev-parse", revision], cwd=REPO, text=True,
            stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def main():
    source_tree = ast.parse(SOURCE.read_text())
    test_tree = ast.parse(TEST_SOURCE.read_text())
    source_fn = next(node for node in source_tree.body
                     if isinstance(node, ast.FunctionDef) and
                     node.name == "input_edge_receipts")
    source_class = next(node for node in test_tree.body
                        if isinstance(node, ast.ClassDef) and
                        node.name == "V39TypedStateFeedbackTests")
    selected = [node for node in source_class.body
                if isinstance(node, ast.FunctionDef) and node.name in NAMES]
    if {node.name for node in selected} != NAMES:
        raise RuntimeError("projection test selection does not match frozen list")
    test_class = ast.ClassDef(
        name="CurrentParentProjectionTests",
        bases=[ast.Attribute(value=ast.Name(id="unittest", ctx=ast.Load()),
                             attr="TestCase", ctx=ast.Load())],
        keywords=[], body=selected, decorator_list=[])
    module = ast.fix_missing_locations(
        ast.Module(body=[source_fn, test_class], type_ignores=[]))
    namespace = {
        "hashlib": hashlib, "json": json, "Path": Path,
        "HERE": DOOM, "product": product, "unittest": unittest,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    namespace["controller"] = type(
        "Controller", (),
        {"input_edge_receipts": staticmethod(namespace["input_edge_receipts"])})()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        namespace["CurrentParentProjectionTests"])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    (ROOT / "raw" / "PARENT_SYNC.stdout").write_text(output)
    metadata = {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "selected_method_count": len(selected),
        "source_sha256": sha256(SOURCE),
        "test_source_sha256": sha256(TEST_SOURCE),
        "previous_branch_head": git_revision("HEAD"),
        "synced_parent_head": git_revision("MERGE_HEAD"),
        "scope": "Source-bound projection tests only; no live X server, GUI, input, game, model, or application-consumption observation.",
    }
    (ROOT / "raw" / "PARENT_SYNC.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    (ROOT / "raw" / "PARENT_SYNC.exit.txt").write_text(
        f"{0 if result.wasSuccessful() else 1}\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    print(output, end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
