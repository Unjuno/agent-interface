import json, tempfile
from pathlib import Path
from audit_map01_terminal_score_agreement_v1 import audit


def write(root, score, rows):
    (root / "score.json").write_text(json.dumps(score))
    (root / "scorer-samples.jsonl").write_text(
        "\n".join(json.dumps(x) for x in rows) + "\n"
    )


def sample(**kw):
    payload = {
        "schema": "independent-progress-sample-v2",
        "map_exit": False,
        "episode_finished": False,
        "player_dead": False,
        "death_count": 0,
        "kill_count": 0,
    }
    payload.update(kw)
    return {"payload": payload, "direct_final_sample": True}


def score():
    return {
        "map_exit": False,
        "episode_finished": False,
        "player_dead": False,
        "death_count": 0,
        "kill_count": 0,
    }


def test_match():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); write(root, score(), [sample()])
        assert audit(root)["pass"] is True


def test_value_mismatch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); s = score(); s["map_exit"] = True; write(root, s, [sample()])
        result = audit(root)
        assert result["pass"] is False
        assert "terminal field disagreement: map_exit" in result["failures"]


def test_type_mismatch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); s = score(); s["map_exit"] = 0; write(root, s, [sample()])
        assert audit(root)["pass"] is False


def test_duplicate_final():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); write(root, score(), [sample(), sample()])
        assert audit(root)["pass"] is False


def test_final_must_be_last():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); final = sample(); periodic = {"payload": dict(final["payload"])}
        write(root, score(), [final, periodic])
        assert audit(root)["pass"] is False


def test_missing_files():
    with tempfile.TemporaryDirectory() as d:
        assert audit(Path(d))["pass"] is False


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("test_")]
    for name, fn in sorted(tests):
        fn(); print("PASS", name)
