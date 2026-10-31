"""Audit the retained WSLc cancel/review/attack attempts."""
import hashlib, json, zipfile
from pathlib import Path
root = Path(__file__).parent
for name in ("ab01", "ab02"):
    with zipfile.ZipFile(root/(name+".zip")) as z:
        def j(path): return json.loads(z.read(path).decode("utf-8-sig"))
        cond, result = j("conditions.json"), j("output/result.json")
        assert hashlib.sha256(z.read("runner.py")).hexdigest() == cond["runner_sha256"]
        assert result["model_calls"] == 0 and result["task_success"] is None
        if name == "ab01":
            assert result["status"] == "error" and not result["cancel_monitor"]["held_observed"]
            assert result["finally_close"]["release"]["verified"]
            assert not result["finally_close"]["release"]["keys_down"]
            assert "cancel_result" not in result
            print("ab01: held input not observed; owner-close release verified; worker outcome not retained")
            continue
        assert result["status"] == "completed" and result["benchmark_frames"] == 20
        assert result["keys_down_after"] == []
        mon, action = result["cancel_monitor"], result["cancel_result"]
        assert mon["held_observed"] and mon["response"]["status"] == "cancel_requested"
        assert mon["response"]["review_required"] is True
        assert action["status"] == "execution_failed"
        release = action["execution"]["releases"][-1]
        assert release["verified"] and not release["keys_down"] and not release["buttons_down"]
        assert mon["held_ns"] <= mon["request_ns"] <= release["monotonic_ns"]
        review = j("output/review.json")
        assert review["status"] == "reviewed" and review["binding_revision"] > review["previous_binding_revision"]
        assert release["monotonic_ns"] <= review["started_ns"]
        stale = j("output/stale.json")
        assert stale["status"] == "refused" and stale["input_dispatched"] is False
        assert len(result["actions"]) == 3
        for item in result["actions"]:
            assert item["status"] == "completed" and item["execution"]["releases"]
            assert all(x["verified"] and not x["keys_down"] and not x["buttons_down"] for x in item["execution"]["releases"])
        fire = j("output/action-benchmark_fire.json")
        assert fire == result["actions"][-1] and fire["execution"]["waits"][0]["requested_ms"] == 1000
        assert review["ended_ns"] <= fire["execution"]["started_ns"]
        before = next(s for s in result["samples"] if s["label"] == "before_benchmark_fire")
        after = next(s for s in result["samples"] if s["label"] == "after_benchmark_fire")
        assert before["kills"] == 0 and after["kills"] == 1
        frames = j("output/benchmark/frames.json")
        assert len(frames) == 20
        for row in frames:
            data = z.read("output/benchmark/frame-%02d.png" % row["index"])
            assert hashlib.sha256(data).hexdigest() == row["sha256"]
        for i in (0, 4): assert any(x["id"] == 14 and x["name"] == "Zombieman" for x in frames[i]["labels"])
        for i in (5, 19): assert any(x["id"] == 14 and x["name"] == "DeadZombieman" for x in frames[i]["labels"])
        final = result["close"]["release"]
        assert final["verified"] and not final["keys_down"] and not final["buttons_down"]
        print(json.dumps({"allocation":name,"held":True,"cancel":"execution_failed", "release_verified":True,"review":"reviewed","stale":"refused", "fire":"completed", "kills_before_after":[before["kills"],after["kills"]], "target_id_14":"Zombieman -> DeadZombieman", "cancel_to_release_ms":(release["monotonic_ns"]-mon["request_ns"])/1e6,"final_keys_down":result["keys_down_after"]},indent=2))
