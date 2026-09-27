#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def canonical_sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_fixture(path=None):
    p = pathlib.Path(path) if path else HERE / "fixture.json"
    return json.loads(p.read_text(encoding="utf-8"))


def validate_geometry(g):
    if not isinstance(g, list) or len(g) != 4 or any(type(v) is not int for v in g):
        raise ValueError("malformed_geometry")
    if g[2] <= 0 or g[3] <= 0:
        raise ValueError("malformed_geometry")


def translate(points, dx, dy):
    out = []
    for point in points:
        if not isinstance(point, list) or len(point) != 2 or any(type(v) is not int for v in point):
            raise ValueError("malformed_point")
        out.append([point[0] + dx, point[1] + dy])
    return out


def compile_macro(source):
    allowed = {"screen_chrome", "window_content"}
    if set(source) != {"source_geometry", "screen_chrome", "window_content", "branch"}:
        raise ValueError("unknown_source_field")
    validate_geometry(source["source_geometry"])
    if set(source["branch"]) != {"met", "target_not_reached"}:
        raise ValueError("unknown_branch")
    if source["branch"] != {"met": "CONTINUE", "target_not_reached": "YIELD"}:
        raise ValueError("unknown_branch")
    frames = set()
    if source["screen_chrome"]:
        frames.add("screen_chrome")
    if source["window_content"]:
        frames.add("window_content")
    if frames != allowed:
        raise ValueError("unknown_frame")
    return {
        "format": "guarded-framed-macro-v1",
        "source_geometry": source["source_geometry"],
        "frames": ["screen_chrome", "window_content"],
        "screen_chrome": source["screen_chrome"],
        "window_content": source["window_content"],
        "branch": source["branch"],
        "binding_dependency": "current_pointer_binding_exact_at_use",
        "authority": "none",
        "task_input_granted": False
    }


def literal_replay(source, state):
    if state["kind"] == "ordinary":
        return {
            "decision": source["branch"][state["retained_reason"]],
            "screen_chrome": source["screen_chrome"],
            "first_path": source["window_content"]["first_path"],
            "continuation_path": source["window_content"]["continuation_path"],
            "binding_checked": False,
            "pointer_target_emitted": True,
            "authority": "none",
            "task_input_granted": False
        }
    return {
        "decision": "RAW_NO_BINDING_GUARD",
        "screen_chrome": source["screen_chrome"],
        "first_path": source["window_content"]["first_path"],
        "continuation_path": source["window_content"]["continuation_path"],
        "binding_checked": False,
        "pointer_target_emitted": True,
        "authority": "none",
        "task_input_granted": False
    }


def guarded_replay(macro, state):
    source_geometry = macro["source_geometry"]
    validate_geometry(source_geometry)
    if state["kind"] == "binding_fault":
        validate_geometry(state["resolved_geometry"])
        validate_geometry(state["current_geometry"])
        if state["current_geometry"] != state["resolved_geometry"]:
            return {
                "decision": "YIELD_BINDING_CHANGED",
                "binding_checked": True,
                "pointer_target_emitted": False,
                "authority": "none",
                "task_input_granted": False
            }
        current = state["current_geometry"]
    elif state["kind"] == "ordinary":
        current = state.get("current_geometry")
        if current is None:
            return {
                "decision": "YIELD_BINDING_MISSING",
                "binding_checked": True,
                "pointer_target_emitted": False,
                "authority": "none",
                "task_input_granted": False
            }
        validate_geometry(current)
    else:
        raise ValueError("unknown_state_kind")
    dx, dy = current[0] - source_geometry[0], current[1] - source_geometry[1]
    reason = state["retained_reason"]
    if reason not in macro["branch"]:
        raise ValueError("unknown_branch_reason")
    return {
        "decision": macro["branch"][reason],
        "translation": {"screen_chrome": [0,0], "window_content": [dx,dy]},
        "screen_chrome": macro["screen_chrome"],
        "first_path": translate(macro["window_content"]["first_path"], dx, dy),
        "continuation_path": translate(macro["window_content"]["continuation_path"], dx, dy),
        "binding_checked": True,
        "pointer_target_emitted": True,
        "authority": "none",
        "task_input_granted": False
    }


def score_row(arm, state, out, source):
    row = {"state": state["id"], "arm": arm, "output": out}
    if state["kind"] == "ordinary":
        row.update({
            "first_path_match": out["first_path"] == state["retained_first_path"],
            "continuation_path_match": out["continuation_path"] == state["retained_continuation_path"],
            "chrome_unchanged": out["screen_chrome"] == source["screen_chrome"],
            "branch_match": out["decision"] == source["branch"][state["retained_reason"]],
            "retained_independent_success": state["retained_independent_success"]
        })
    else:
        row.update({
            "fault_refusal_match": (out["decision"] == "YIELD_BINDING_CHANGED" and not out["pointer_target_emitted"])
                if arm == "GUARDED_FRAMED_MACRO" else None,
            "retained_pointer_admissions": state["retained_pointer_admissions"],
            "retained_terminal_status": state["retained_terminal_status"]
        })
    return row


def run(fixture):
    source = fixture["source_procedure"]
    macro = compile_macro(source)
    rows = []
    for state in fixture["states"]:
        rows.append(score_row("LITERAL_RAW_REPLAY", state, literal_replay(source, state), source))
        rows.append(score_row("GUARDED_FRAMED_MACRO", state, guarded_replay(macro, state), source))
    ordinary_guarded = [r for r in rows if r["arm"] == "GUARDED_FRAMED_MACRO" and "first_path_match" in r]
    ordinary_literal = [r for r in rows if r["arm"] == "LITERAL_RAW_REPLAY" and "first_path_match" in r]
    fault_guarded = next(r for r in rows if r["state"] == "1152-binding-fault" and r["arm"] == "GUARDED_FRAMED_MACRO")
    gates = {
        "candidate_path_match_4of4": len(ordinary_guarded) == 4 and all(r["first_path_match"] and r["continuation_path_match"] for r in ordinary_guarded),
        "candidate_branch_match_4of4": len(ordinary_guarded) == 4 and all(r["branch_match"] for r in ordinary_guarded),
        "candidate_chrome_unchanged_4of4": len(ordinary_guarded) == 4 and all(r["chrome_unchanged"] for r in ordinary_guarded),
        "literal_content_mismatch_4of4": len(ordinary_literal) == 4 and all(not r["first_path_match"] and not r["continuation_path_match"] for r in ordinary_literal),
        "literal_chrome_unchanged_4of4": len(ordinary_literal) == 4 and all(r["chrome_unchanged"] for r in ordinary_literal),
        "candidate_binding_fault_refusal": fault_guarded["fault_refusal_match"] is True,
        "candidate_no_authority_all_rows": all(r["output"]["authority"] == "none" and r["output"]["task_input_granted"] is False for r in rows),
        "row_count_10": len(rows) == 10
    }
    passed = all(gates.values())
    return {
        "task": fixture["task"],
        "formal_invocations": 1,
        "formal_reruns": 0,
        "source_blobs": fixture["source_blobs"],
        "compiled_macro": macro,
        "rows": rows,
        "gates": gates,
        "decision": "PASS_OPENTTD_GUARDED_MACRO_TRANSFER_SCOPED" if passed else "FAIL_OR_HOLD_OPENTTD_GUARDED_MACRO_TRANSFER",
        "passed": passed,
        "scope": "deterministic retained-evidence representation replay only; no new OpenTTD/model/input/task-effect execution"
    }


def self_test():
    f = load_fixture()
    m = compile_macro(f["source_procedure"])
    toy = {"id":"toy", "kind":"ordinary", "current_geometry":[129,40,1024,720], "retained_reason":"met"}
    o = guarded_replay(m, toy)
    assert o["first_path"] == f["source_procedure"]["window_content"]["first_path"]
    missing = dict(toy); missing.pop("current_geometry")
    assert guarded_replay(m, missing)["decision"] == "YIELD_BINDING_MISSING"
    fault = {"id":"f", "kind":"binding_fault", "resolved_geometry":[1,2,3,4], "current_geometry":[2,2,3,4]}
    assert guarded_replay(m, fault)["decision"] == "YIELD_BINDING_CHANGED"
    bad = json.loads(json.dumps(f["source_procedure"])); bad["branch"]["met"] = "GUESS"
    try: compile_macro(bad)
    except ValueError: pass
    else: raise AssertionError("bad branch accepted")
    print(json.dumps({"self_test":"PASS"}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--fixture")
    ap.add_argument("--output")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    result = run(load_fixture(a.fixture))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.output:
        pathlib.Path(a.output).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)

if __name__ == "__main__": main()
