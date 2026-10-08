"""Saved-only physical/event/timing oracle; never imports the producer."""
import argparse
import hashlib
import json
from pathlib import Path

def need(value, message):
    if not value: raise ValueError(message)

def down(sample, code):
    bits = bytes.fromhex(sample["keymap"])
    need(len(bits) == 32, "keymap length")
    return bool(bits[code // 8] & (1 << (code % 8)))

def audit(rows, plan):
    expected = {cell["id"]: cell for cell in plan["cells"]}
    need(len(rows) == len(expected) == 12 and len({r["id"] for r in rows}) == 12, "cell membership")
    summary, discriminated = [], True
    for row in rows:
        need({k: row[k] for k in ("id", "repeat", "policy", "blocked")} == expected.get(row["id"]), "cell assignment")
        need(row["error"] is None and row["auto_repeat_disabled"] and row["xvfb_exit"] in (0,-15), "exposure/cleanup error")
        code, times, samples = row["keycode"], row["times"], row["samples"]
        need(type(code) is int and 8 <= code <= 255, "physical keycode")
        need(len(samples) >= 2 and all(type(s["at_ns"]) is int for s in samples)
             and all(a["at_ns"] <= b["at_ns"] for a,b in zip(samples,samples[1:])), "sample chronology")
        need(down(samples[0], code), "first sample must witness held key")
        need(samples[0].get("tag") == "writer_entry", "source writer witness tag")
        checks = [s for s in samples if s.get("tag") == "checkpoint"]
        need(len(checks) == 1 and checks[0]["at_ns"] == times["checkpoint"] == row["checkpoint"]["sample_at_ns"]
             and down(checks[0], code) == row["checkpoint"]["down"], "checkpoint physical sample join")
        ends = [s for s in samples if s.get("tag") == "terminal"]
        need(len(ends) == 1 and {k:ends[0][k] for k in ("keymap","buttons")} == row["terminal"], "terminal physical sample join")
        need(not any(bytes.fromhex(row["terminal"]["keymap"])) and row["terminal"]["buttons"] == 0, "terminal neutral")
        app = row["app_events"]
        need([e["kind"] for e in app] == ["press","release"] and all(e["keycode"] == code for e in app), "app press/release/late input")
        need(app[0]["at_ns"] <= app[1]["at_ns"], "app event order")
        execution = row["program"]["execution"]
        program = row["program_input"]
        need(program["schema"] == "agent-interface/program-v1" and program["program_id"] == row["id"]
             and program["source"] == {"observation_seq":1,"binding_revision":0}
             and program["terminal"] == {"release_all_required":True}
             and program["authority"]["lease_id"] == "owned-6999"
             and program["authority"]["expires_at_ns"] > times["program_return"]
             and program["ops"] == [{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},
                {"op":"observe","frame":"window_client","x":0,"y":0,"w":280,"h":180},{"op":"release_all"}], "public program identity")
        need(row["program"]["status"] == "completed" and row["program"]["admission"] == "accepted"
             and execution["completed_ops"] == [0,1,2,3] and execution["program_emissions"] == 2, "public program result")
        need(bool(execution["releases"]) and all(r.get("verified") is True and r.get("keys_down") == []
             and r.get("buttons_down") == [] for r in execution["releases"]), "false release receipt")
        need(times["write_enter"] <= times["write_resume"] <= times["write_return"] <= times["program_return"], "write/program order")
        need(times["checkpoint"] >= times["cancel_request"] + plan["checkpoint_after_request_ns"], "early checkpoint")
        png = row["png"]; pt = png["timing_ns"]
        need(png["bytes"] > 0 and png["header"] == "89504e470d0a1a0a", "actual PNG bytes")
        need(row["png_write_payload"] == {k:png[k] for k in ("bytes","header","sha256")}, "writer payload identity")
        source = row["source_capture"]
        need(source["operation_index"] == 2 and source["sha256"] == png["source_raw_sha256"]
             and source["capture_started_ns"] <= source["capture_ended_ns"] <= pt["started"]
             and (png["width"],png["height"]) == (280,180), "source capture identity/times")
        need(pt["started"] <= pt["converted"] <= pt["encoded"] <= times["write_enter"]
             <= times["write_return"] <= pt["written"] <= pt["hashed"], "actual artifact writer stack/times")
        need(row["write_stack"].count("write") >= 2 and "capture" in row["write_stack"], "actual source writer stack")
        first_up = next((s for s in samples if not down(s, code)), None)
        need(first_up is not None, "no physical release sample")
        if row["policy"] == "separate":
            cleanup = row["cleanup_response"]
            need(cleanup["verified"] is True and cleanup["keys_down"] == [] and cleanup["buttons_down"] == [], "cleanup-only release verified")
        if row["blocked"]:
            need(times["write_resume"] >= times["cancel_request"] + plan["stall_after_request_ns"], "fault exposure too short")
            need(times["write_enter"] <= times["cancel_request"] < times["checkpoint"] < times["write_resume"], "blocked chronology")
            need(row["checkpoint"]["writer_pending"] and row["checkpoint"]["program_pending"], "not blocked at checkpoint")
            if row["policy"] == "coupled":
                ok = row["checkpoint"]["down"] and first_up["at_ns"] >= times["write_resume"]
            else:
                ok = not row["checkpoint"]["down"] and first_up["at_ns"] < times["checkpoint"]
            discriminated &= ok
        else:
            need(not row["checkpoint"]["down"] and not row["checkpoint"]["writer_pending"]
                 and not row["checkpoint"]["program_pending"], "healthy control not complete")
        summary.append({"id":row["id"], "policy":row["policy"], "blocked":row["blocked"],
                        "checkpoint_down":row["checkpoint"]["down"],
                        "first_confirmed_up_after_request_ms":(first_up["at_ns"]-times["cancel_request"])/1e6,
                        "write_return_after_request_ms":(times["write_return"]-times["cancel_request"])/1e6})
    return {"status":"PASS_PUBLIC_X11_PNG_RELEASE_BOUNDARY_SCOPED" if discriminated else "HOLD_NO_PHYSICAL_RELEASE_DISCRIMINATOR",
            "rows":summary, "n":12, "hard_deadline_established":False, "production_plane_integrated":False}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("raw"); parser.add_argument("plan"); parser.add_argument("out"); args=parser.parse_args()
    raw=Path(args.raw); rows=[json.loads(line) for line in raw.read_text().splitlines()]
    result=audit(rows,json.loads(Path(args.plan).read_text()))
    for row in rows:
        png=raw.parent/row["png"]["file"]
        need(png.is_file() and hashlib.sha256(png.read_bytes()).hexdigest() == row["png"]["sha256"], "saved PNG identity")
        need(png.read_bytes()[:8].hex() == row["png"]["header"] and png.stat().st_size == row["png"]["bytes"], "saved PNG size/header")
    result["raw_sha256"]=hashlib.sha256(raw.read_bytes()).hexdigest()
    with Path(args.out).open("x") as stream: json.dump(result,stream,indent=2); stream.write("\n")
    print(json.dumps(result))

if __name__ == "__main__": main()
