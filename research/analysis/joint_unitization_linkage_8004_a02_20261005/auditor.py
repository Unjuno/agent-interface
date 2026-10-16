"""Independent auditor; reads oracle.json, unlike candidate.py."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def _oracle_histogram(oracle, channels):
    counts = Counter()
    record_truth = oracle["record_truth"]
    by_opp = defaultdict(set)
    for record_id, opp in record_truth.items():
        record = oracle["records"][record_id]
        by_opp[opp].add(record["channel"])
    for opportunity in oracle["opportunities"]:
        oid = opportunity["opportunity_id"]
        detected = by_opp.get(oid, set())
        mask = opportunity["observable_channels"]
        vector = "".join("?" if ch not in mask else ("1" if ch in detected else "0") for ch in channels)
        counts[vector] += 1
    return counts, by_opp


def audit(observations, oracle, candidate):
    errors = []
    channels = observations["channels"]
    records = {r["record_id"]: r for r in observations["raw_records"]}
    record_truth = oracle["record_truth"]
    def contains_oracle_field(value):
        if isinstance(value, dict):
            return any(any(token in str(k).lower() for token in ("truth", "oracle", "opportunity_id")) or contains_oracle_field(v) for k, v in value.items())
        if isinstance(value, list):
            return any(contains_oracle_field(v) for v in value)
        return False
    if contains_oracle_field(observations):
        errors.append("oracle_leak_in_candidate_input")
    if set(oracle["record_truth"]) != set(records):
        errors.append("oracle_record_denominator")
    if set(oracle["records"]) != set(records):
        errors.append("oracle_raw_record_coverage")
    opp_ids = [o["opportunity_id"] for o in oracle["opportunities"]]
    if len(opp_ids) != len(set(opp_ids)) or len(opp_ids) != 6:
        errors.append("latent_opportunity_denominator")
    if not set(record_truth.values()) <= set(opp_ids):
        errors.append("record_truth_foreign_opportunity")
    oracle_expected = {o["opportunity_id"]: set(o["expected_channels"]) for o in oracle["opportunities"]}
    oracle_observed = defaultdict(set)
    for record_id, opportunity_id in record_truth.items():
        oracle_observed[opportunity_id].add(oracle["records"][record_id]["channel"])
    if any(oracle_observed[oid] != expected for oid, expected in oracle_expected.items()):
        errors.append("oracle_expected_detection_mismatch")
    expected_ids = {
        f"{s}+{l}"
        for s in observations["segmentation_alternatives"]
        for l in observations["linkage_alternatives"]
    }
    rows = candidate.get("assignments", [])
    actual_ids = [r.get("assignment") for r in rows]
    if candidate.get("assignment_count") != len(expected_ids) or set(actual_ids) != expected_ids or len(actual_ids) != len(set(actual_ids)):
        errors.append("assignment_space_denominator")

    # Auditor independently reconstructs components with an adjacency traversal.
    components_by_assignment = {}
    false_links = Counter()
    false_merges = Counter()
    false_splits = Counter()
    missed_opportunity_links = Counter()
    for row in rows:
        seg = observations["segmentation_alternatives"].get(row.get("segmentation"))
        link = observations["linkage_alternatives"].get(row.get("linkage"))
        if seg is None or link is None:
            errors.append("unknown_assignment_label")
            continue
        unit_of = {}
        unit_members = {}
        for ch in channels:
            for ix, group in enumerate(seg[ch]):
                uid = f"{ch}:{ix}"
                unit_members[uid] = list(group)
                for rid in group:
                    if rid not in records or records[rid]["channel"] != ch or rid in unit_of:
                        errors.append("segmentation_partition")
                    unit_of[rid] = uid
        if set(unit_of) != set(records):
            errors.append("segmentation_raw_coverage")
        graph = defaultdict(set)
        for uid in unit_members:
            graph[uid]
        for left, right in link:
            if left not in unit_of or right not in unit_of:
                errors.append("link_endpoint")
                continue
            if records[left]["channel"] == records[right]["channel"]:
                errors.append("within_channel_link")
            graph[unit_of[left]].add(unit_of[right])
            graph[unit_of[right]].add(unit_of[left])
            if record_truth.get(left) != record_truth.get(right):
                false_links[row["assignment"]] += 1
        comps = []
        seen = set()
        for uid in graph:
            if uid in seen:
                continue
            stack, members = [uid], set()
            seen.add(uid)
            while stack:
                cur = stack.pop()
                members.update(unit_members[cur])
                for nxt in graph[cur]:
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            comps.append(sorted(members))
        canon = sorted(comps)
        supplied = sorted(sorted(c.get("records", [])) for c in row.get("components", []))
        if supplied != canon or len(canon) != row.get("component_count"):
            errors.append("candidate_component_reconstruction")
        supplied_records = [rid for comp in supplied for rid in comp]
        if len(supplied_records) != len(records) or set(supplied_records) != set(records) or len(supplied_records) != len(set(supplied_records)):
            errors.append("raw_record_conservation")
        rebuilt_hist = Counter()
        for comp in canon:
            vector = "".join("1" if any(records[r]["channel"] == ch for r in comp) else "0" for ch in channels)
            rebuilt_hist[vector] += 1
        if dict(sorted(rebuilt_hist.items())) != row.get("capture_histogram"):
            errors.append("candidate_capture_histogram")
        if sum(len(c) for c in canon) != len(records) or len([r for c in canon for r in c]) != len(set(r for c in canon for r in c)):
            errors.append("raw_record_conservation")
        components_by_assignment[row["assignment"]] = canon
        for comp in canon:
            truths = {record_truth[r] for r in comp}
            if len(truths) > 1:
                false_merges[row["assignment"]] += 1
        opp_to_components = defaultdict(set)
        for ix, comp in enumerate(canon):
            for rid in comp:
                opp_to_components[record_truth[rid]].add(ix)
        false_splits[row["assignment"]] = sum(len(indices) > 1 for indices in opp_to_components.values())
        for opp in oracle["opportunities"]:
            oid = opp["opportunity_id"]
            opp_records = [r for r, truth in record_truth.items() if truth == oid]
            if len({records[r]["channel"] for r in opp_records}) > 1:
                if len(opp_to_components.get(oid, set())) > 1:
                    missed_opportunity_links[row["assignment"]] += 1

    truth_hist, by_opp = _oracle_histogram(oracle, channels)
    status_counts = Counter(o["availability"] for o in oracle["opportunities"])
    all_channel_zero = truth_hist.get("0" * len(channels), 0)
    signatures = {(r.get("component_count"), json.dumps(r.get("capture_histogram"), sort_keys=True)) for r in rows}
    expected_disp = "UNIDENTIFIED" if len(signatures) > 1 else "STABLE_WITHIN_AUTHORED_SET"
    if candidate.get("disposition") != expected_disp:
        errors.append("unidentified_label")
    if "unseen_event_count" in candidate or candidate.get("unseen_event_count") == 0:
        errors.append("unsupported_unseen_count")
    return {
        "ok": not errors,
        "errors": errors,
        "assignment_count_reconstructed": len(components_by_assignment),
        "latent_opportunity_denominator": len(opp_ids),
        "oracle_capture_history_counts": dict(sorted(truth_hist.items())),
        "oracle_all_channel_zero_count": all_channel_zero,
        "fully_observed_opportunity_denominator": sum(len(o["observable_channels"]) == len(channels) for o in oracle["opportunities"]),
        "availability_status_counts": dict(sorted(status_counts.items())),
        "false_links_by_assignment": dict(sorted(false_links.items())),
        "false_merges_by_assignment": dict(sorted(false_merges.items())),
        "false_splits_by_assignment": dict(sorted(false_splits.items())),
        "missed_multichannel_opportunities_by_assignment": dict(sorted(missed_opportunity_links.items())),
        "scope": "authored finite construction only; no population estimator or calibrated uncertainty",
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--observations", required=True)
    p.add_argument("--oracle", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    obs = json.loads(Path(a.observations).read_text())
    oracle = json.loads(Path(a.oracle).read_text())
    cand = json.loads(Path(a.candidate).read_text())
    result = audit(obs, oracle, cand)
    Path(a.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": result["ok"], "errors": result["errors"], "opportunities": result["latent_opportunity_denominator"]}, sort_keys=True))
