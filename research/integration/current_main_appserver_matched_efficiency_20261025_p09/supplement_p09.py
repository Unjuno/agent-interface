"""Re-score retained P09 owner/provider evidence without changing outcomes."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
GREEN = (12, 3, 20, 13)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def score(run):
    result = json.loads((run / "RESULT.json").read_text(encoding="utf-8"))
    arm = result.get("arm") or run.name.split("-", 1)[1]
    selected = json.loads((run / "model-selected-point.json").read_text(encoding="utf-8"))
    provider = json.loads((run / "provider-call" / "result.json").read_text(encoding="utf-8"))
    server = run / "server"
    click_files = list(server.rglob("synthetic-target-click.json"))
    effect_files = list(server.rglob("synthetic-effect-receipt.json"))
    mint_files = list(server.rglob("mint-grounded_green.json"))
    close_files = list(server.glob("*-close.json"))
    click = json.loads(click_files[0].read_text(encoding="utf-8")) if len(click_files) == 1 else None
    effect = json.loads(effect_files[0].read_text(encoding="utf-8")) if len(effect_files) == 1 else None
    mint = json.loads(mint_files[0].read_text(encoding="utf-8")) if len(mint_files) == 1 else None
    close = json.loads(close_files[0].read_text(encoding="utf-8")) if len(close_files) == 1 else None
    point = selected.get("point")
    observed_seq = selected.get("observation_sequence")
    clicked = click.get("event", {}).get("point") if click else None
    pixel = list(Image.frombytes("RGB", (32, 32), (run / "final-framebuffer.bgrx").read_bytes(), "raw", "BGRX").getpixel((1, 1)))
    obs_hash = sha((run / "observed-public-mcp.png").read_bytes())
    public = run / ("public-direct-response.json" if arm == "direct_public_input" else "public-compiled-response.json")
    action_envelope = json.loads(public.read_text(encoding="utf-8"))
    action_returned = action_envelope.get("status") == "returned"
    observation_files = list(server.glob("guarded-session-*/observation-1.json"))
    observation = json.loads(observation_files[0].read_text(encoding="utf-8")) if len(observation_files) == 1 else {}
    action_latency = result.get("observation_to_action_return_ms")
    if action_latency is None and observation.get("capture_ns") and action_envelope.get("sdk_return_ns"):
        action_latency = (action_envelope["sdk_return_ns"] - observation["capture_ns"]) / 1e6
    in_target = lambda p: type(p) is list and len(p) == 2 and GREEN[0] <= p[0] <= GREEN[2] and GREEN[1] <= p[1] <= GREEN[3]
    checks = {
        "one_completed_provider_turn": provider.get("turn_status") == "completed" and provider.get("answer_eligible") is True,
        "provider_usage_reported": isinstance(provider.get("usage"), dict) and all(type(provider["usage"].get(k)) is int for k in ("input_tokens", "output_tokens", "reasoning_output_tokens")),
        "public_action_returned": action_returned,
        "exact_model_image": selected.get("image_sha256") == obs_hash and (result.get("observation_image_sha256") is None or result.get("observation_image_sha256") == obs_hash),
        "model_point_in_green": in_target(point),
        "owner_click_is_selected_point": click is not None and clicked == point and in_target(clicked),
        "exactly_one_owner_effect": len(click_files) == 1 and len(effect_files) == 1 and effect is not None and effect.get("button_press_count") == 1,
        "expected_persisted_pixel": pixel == [255, 0, 0] and effect is not None and effect.get("rgb") == [255, 0, 0],
        "mint_sequence_matches_observation": mint is not None and mint.get("created_sequence") == observed_seq,
        "verified_release_and_close": result.get("release_verified") is True or (close is not None and close.get("verified") is True and close.get("release_confirmed") is True),
    }
    score = {
        "schema": "agent-interface/p09-retained-evidence-supplemental-score-v1",
        "pair": result.get("pair") or run.name.split("-", 1)[0], "arm": arm,
        "original_result_classification": result.get("classification"),
        "independent_task_success_from_retained_evidence": all(checks.values()),
        "checks": checks,
        "usage": provider.get("usage"),
        "provider_turn_ms": result.get("provider_turn_ms", provider.get("runner_ns", 0) / 1e6),
        "observation_to_action_return_ms": action_latency,
        "total_trial_ms": result.get("total_trial_ms"),
        "wslc_used": False, "physical_input": False,
        "scope": "post-hoc independent audit of original immutable evidence; no replay or replacement",
    }
    (run / "SUPPLEMENTAL-SCORE.json").write_text(json.dumps(score, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")
    return score

def main():
    rows=[]
    for run in sorted((ROOT / "run").iterdir()):
        if run.is_dir() and (run / "RESULT.json").is_file():
            rows.append(score(run))
    print(json.dumps(rows, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
