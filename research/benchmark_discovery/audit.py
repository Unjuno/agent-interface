#!/usr/bin/env python3
"""Audit archived feasibility evidence without launching games."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    harnesses = {digest(p): p.name for p in HERE.glob("smoke*.py")}
    plans = {digest(p): p.name for p in HERE.glob("plan*.json")}
    rows = []
    for path in sorted((HERE / "results").glob("*/*/manifest.json")):
        manifest = json.loads(path.read_text())
        assert manifest["harness_sha256"] in harnesses, path
        assert manifest["plan_sha256"] in plans, path
        cases = json.loads((path.parent / "results.json").read_text())
        assert len(cases) == 2
        for row in cases:
            run = path.parent / str(row["attempt"])
            assert row == json.loads((run / "result.json").read_text())
            assert row["all_owned_processes_exited"]
            if "screen_sha256" in row:
                assert digest(run / "screen.png") == row["screen_sha256"]
            metrics = {}
            # Crashed/zombie processes are excluded, never reported as cheap live apps.
            if row["pre_cleanup_returncode"] is None and "resources" in row:
                m = row["resources"]
                for role, pid in m["roles"].items():
                    k = str(pid)
                    b, a = m["before"][k], m["after"][k]
                    assert b is not None and a is not None
                    metrics[role] = {
                        "cpu_percent_one_core": round((a["cpu_s"] - b["cpu_s"]) / row["sample_seconds"] * 100, 2),
                        "sampled_max_rss_mib": round(max(x[k]["rss_bytes"] for x in m["samples"] if x[k]) / 2**20, 2)}
            rows.append({"cohort": path.parent.relative_to(HERE / "results").as_posix(),
                         "attempt": row["attempt"], "harness": harnesses[manifest["harness_sha256"]],
                         "mapped_window": bool(row["windows"]),
                         "alive_before_cleanup": row["pre_cleanup_returncode"] is None,
                         "forced_kill": row.get("forced_kill"), "resources": metrics})

    mp = HERE / "results/linux-feasibility-05/mindustry"
    ma, mb = [json.loads((mp / str(i) / "oracle-baseline.json").read_text()) for i in (1, 2)]
    assert (ma["width"], ma["height"]) == (250, 300)
    changes = [0] * 5
    changed_tiles = 0
    for ra, rb in zip(ma["tiles"], mb["tiles"]):
        for a, b in zip(ra, rb):
            changed_tiles += a != b
            for k in range(5):
                changes[k] += a[k] != b[k]
    assert changed_tiles == 10817, changed_tiles
    assert all(x["core_present"] and x["copper"] == 200 for x in (ma, mb))
    # This discrepancy is a discovery result, not an audit failure.
    mindustry = {"initial_tiles": 75000, "different_tiles": changed_tiles,
                 "different_fields_floor_block_overlay_team_rotation": changes,
                 "rotation_not_measured": True,
                 "complete_state_determinism": "not established; recorded tile states differ"}
    ot = HERE / "results/linux-feasibility-07/openttd"
    grids = []
    for i in (1, 2):
        lines = (ot / str(i) / "stderr.txt").read_text().splitlines()
        grid = [x.split("AIFS_ROW ", 1)[1] for x in lines if "AIFS_ROW " in x]
        assert len(grid) == 64
        assert any("AIFS_READY 64 64" in x for x in lines)
        values = [x.split("AIFS_TARGET_OWNED_ROAD_COUNT ", 1)[1] for x in lines if "AIFS_TARGET_OWNED_ROAD_COUNT " in x]
        assert values and set(values) == {"0"}
        grids.append(grid)
    assert grids[0] == grids[1]
    openttd = {"rows": 64, "tiles": 4096, "recorded_initial_state_equal": True,
               "scope": "height, ownership and road presence only; not full engine state",
               "sha256": hashlib.sha256("\n".join(grids[0]).encode()).hexdigest(),
               "negative_road_oracle": True, "positive_control": "not run"}
    lp = HERE / "results/linux-feasibility-04/luanti"
    for i in (1, 2):
        for label in ("baseline", "sample", "final"):
            d = json.loads((lp / str(i) / "world" / f"oracle-{label}.json").read_text())
            assert d["ready"] and d["target_count"] == 0 and not d["task_success"]
            if label != "final":
                assert d["player_pos"] == {"x": 0, "y": 2, "z": 4}
    luanti = {"baseline_and_sample_pose_equal": True, "negative_node_oracle": True,
               "gravity": 0, "positive_control": "not run", "navigation": "not evaluated"}
    return {"scope": "discovery smoke, no benchmark adoption or runtime qualification",
            "attempts": len(rows), "all_owned_processes_exited": True,
            "runs": rows, "mindustry": mindustry, "openttd": openttd, "luanti": luanti}


if __name__ == "__main__":
    result = audit()
    (HERE / "audit-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "runs"}, indent=2))
