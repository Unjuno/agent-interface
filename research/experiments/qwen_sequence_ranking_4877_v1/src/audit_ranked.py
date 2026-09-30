import argparse
import hashlib
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from candidates import candidates_from_state
from protocol import bind_intent, simulate_bound
from runner import format_prompt, score_path

MODEL = "/hf/model"
ADAPTER = "/study/assets"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--raw", required=True)
    args = ap.parse_args()
    raw_in = Path(args.input).read_bytes()
    raw = json.loads(Path(args.raw).read_bytes())
    if raw["input_sha256"] != sha(raw_in):
        raise SystemExit("AUDIT_FAIL_INPUT_HASH")
    data = json.loads(raw_in)
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True, torch_dtype=torch.float32,
                                                attn_implementation="eager", device_map={"": "cpu"})
    model = PeftModel.from_pretrained(base, ADAPTER, is_trainable=False, local_files_only=True).eval()
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    checks = {"input_hash": True, "rows": len(data["rows"]) == len(raw["rows"]),
              "candidate_sets": True, "independent_scores": True, "ranking": True,
              "effects": True, "controls": {}}
    for item, got in zip(data["rows"], raw["rows"]):
        row, candidates = item["row"], item["candidates"]
        if candidates != candidates_from_state(row["state"]):
            checks["candidate_sets"] = False
        if got["case_id"] != row["case_id"] or [s["candidate"] for s in got["candidate_scores"]] != candidates:
            checks["candidate_sets"] = False
        prompt = format_prompt(tok, row["prompt"])
        pids = tok.encode(prompt, add_special_tokens=False)
        scores = []
        for cand in candidates:
            cids = tok.encode(cand, add_special_tokens=False)
            lps = score_path(model, pids, cids, tok.eos_token_id, torch.device("cpu"))
            scores.append({"candidate": cand, "token_logprobs": lps, "sum_logprob": sum(lps)})
        if len(scores) != len(got["candidate_scores"]) or any(
                abs(x["sum_logprob"] - y["sum_logprob"]) > 1e-5 for x, y in zip(scores, got["candidate_scores"])):
            checks["independent_scores"] = False
        ranked = sorted(candidates, key=lambda c: (-next(x["sum_logprob"] for x in scores if x["candidate"] == c), c))
        if ranked != got["ranked_candidates"]:
            checks["ranking"] = False
        if len(got["outputs"]) != 3:
            checks["effects"] = False
        for output in got["outputs"]:
            bound = bind_intent(json.loads(output["text"]) if output["arm"] == "ranked" else _parse(output["text"]),
                                row["state"], row["requested_generation"])
            effect = simulate_bound(bound, row["state"])
            if bound != output["bound"] or effect != output["effect"]:
                checks["effects"] = False
            if effect.get("changed") and bound.get("status") == "BOUND":
                args_out = bound.get("arguments", {})
                if args_out.get("scope_id") != row["state"].get("scope_id") or args_out.get("generation") != row["state"].get("generation"):
                    checks["controls"]["identity_spoof"] = False
    # Mutate real algorithm outputs one at a time, then verify the actual audit gates reject them.
    def audit_probe(probe):
        if probe["input_sha256"] != sha(raw_in): return False
        for item, got in zip(data["rows"], probe["rows"]):
            if [x["candidate"] for x in got["candidate_scores"]] != item["candidates"]: return False
            for score in got["candidate_scores"]:
                if not isinstance(score["sum_logprob"], (int, float)): return False
            if sorted(got["ranked_candidates"]) != sorted(item["candidates"]): return False
            ranked_scores = {x["candidate"]: x["sum_logprob"] for x in got["candidate_scores"]}
            expected = sorted(item["candidates"], key=lambda c: (-ranked_scores[c], c))
            if got["ranked_candidates"] != expected: return False
            for output in got["outputs"]:
                parsed = _parse(output["text"])
                bound = bind_intent(parsed, item["row"]["state"], item["row"]["requested_generation"])
                if bound != output["bound"] or simulate_bound(bound, item["row"]["state"]) != output["effect"]: return False
        return True

    corruptions = {
        "input_hash": lambda x: x.update(input_sha256="bad"),
        "candidate_membership": lambda x: x["rows"][0]["candidate_scores"].pop(),
        "ranking_order": lambda x: x["rows"][0].update(ranked_candidates=list(reversed(x["rows"][0]["ranked_candidates"]))),
        "ranking_score": lambda x: x["rows"][0]["candidate_scores"][0].update(sum_logprob=0.0),
        "output_bound": lambda x: x["rows"][0]["outputs"][0].update(bound={"status":"BOUND"}),
        "output_effect": lambda x: x["rows"][0]["outputs"][0].update(effect={"changed":True}),
    }
    for name, mutate in corruptions.items():
        probe = json.loads(json.dumps(raw)); mutate(probe)
        checks["controls"][name] = not audit_probe(probe)
    passed = all(v for k, v in checks.items() if k != "controls") and all(checks["controls"].values())
    report = {"schema": "qwen-sequence-ranking-audit-v1", "input_sha256": sha(raw_in),
              "raw_sha256": sha(Path(args.raw).read_bytes()), "checks": checks, "passed": passed}
    print(json.dumps(report, sort_keys=True))
    if not passed:
        raise SystemExit("AUDIT_FAIL")


def _parse(text):
    try:
        return json.loads(text)
    except Exception:
        return None


if __name__ == "__main__":
    main()

