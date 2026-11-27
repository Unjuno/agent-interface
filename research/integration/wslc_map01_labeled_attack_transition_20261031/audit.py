"""Audit the retained one-allocation attack-transition pilot."""
import collections, hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path

with zipfile.ZipFile(Path(__file__).with_name("aa04.zip")) as z:
    def j(name): return json.loads(z.read(name).decode("utf-8-sig"))
    c, result, score = j("conditions.json"), j("output/result.json"), j("score.json")
    frames = j("output/benchmark/frames.json")
    assert hashlib.sha256(z.read("runner.py")).hexdigest() == c["runner_sha256"]
    assert hashlib.sha256(z.read("score.py")).hexdigest() == c["scorer_sha256"] == "61ea5e471b914c4ac098d3f06782d02994035d35c2a5ca485ad2d60da8de7a0c"
    assert result["status"] == "completed" and result["model_calls"] == 0
    assert result["task_success"] is None and result["keys_down_after"] == []
    assert len(result["actions"]) == 3
    for action in result["actions"]:
        assert action["status"] == "completed"
        assert all(r["verified"] and not r["keys_down"] and not r["buttons_down"] for r in action["execution"]["releases"])
        assert action["execution"]["releases"]
    assert result["close"]["release"]["verified"]
    fire = j("output/action-benchmark_fire.json")
    assert fire == result["actions"][2]
    assert fire["execution"]["waits"][0]["requested_ms"] == 1000
    assert len(frames) == 20 and [f["index"] for f in frames] == list(range(20))
    for f in frames:
        raw = z.read("output/benchmark/frame-%02d.png" % f["index"])
        assert hashlib.sha256(raw).hexdigest() == f["sha256"]
    before = next(s for s in result["samples"] if s["label"] == "before_benchmark_fire")
    after = next(s for s in result["samples"] if s["label"] == "after_benchmark_fire")
    assert before["kills"] == 0 and after["kills"] == 1
    assert score["status"] == "completed" and score["seed"]["id"] == 14
    labels = [[x["name"] for x in f["labels"] if x["id"] == score["seed"]["id"]] for f in frames]
    assert labels[:5] == [["Zombieman"]] * 5 and labels[5:] == [["DeadZombieman"]] * 15
    with tempfile.TemporaryDirectory() as tmp:
        z.extract("score.py", tmp)
        z.extract("output/benchmark/frames.json", tmp)
        for f in frames: z.extract("output/benchmark/frame-%02d.png" % f["index"], tmp)
        recomputed = json.loads(subprocess.check_output([sys.executable, str(Path(tmp)/"score.py"), str(Path(tmp)/"output/benchmark")]))
    assert recomputed == score
    counts = {m:dict(collections.Counter(r[m]["outcome"] for r in score["rows"])) for m in ("fixed", "wide")}
    print(json.dumps({"audit":"passed", "frames":len(frames), "labels": {"Zombieman":5,"DeadZombieman":15}, "kills_before_after":[before["kills"],after["kills"]], "outcomes":counts, "release_verified":True}, indent=2))
