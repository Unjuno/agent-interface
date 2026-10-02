"""Independent pure-Python scorer used only for the #5008 construction gate."""
import json
import math
import pathlib
import sys


def linear(x, weight, bias):
    return [sum(x[i] * weight[o][i] for i in range(len(x))) + bias[o]
            for o in range(len(bias))]


def predict(artifact, role, x):
    tensors = artifact["tensors"][role]
    if role == "A":
        h = [math.tanh(v) for v in linear(
            x, tensors["enc.0.weight"], tensors["enc.0.bias"])]
        logits = linear(h, tensors["head.weight"], tensors["head.bias"])
    else:
        h = [math.tanh(v) for v in linear(
            x, tensors["core.enc.0.weight"], tensors["core.enc.0.bias"])]
        logits = linear(h, tensors["core.head.weight"], tensors["core.head.bias"])
        low_rank = [sum(h[i] * tensors["a"][i][k] for i in range(len(h)))
                    for k in range(2)]
        residual = [sum(low_rank[k] * tensors["b"][k][c] for k in range(2)) / 2
                    for c in range(4)]
        logits = [base + delta for base, delta in zip(logits, residual)]
    return max(range(len(logits)), key=logits.__getitem__)


def main(root):
    root = pathlib.Path(root)
    artifact = json.loads((root / "skill.json").read_text(encoding="utf-8"))
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))
    summary = {}
    for role, fixture in expected["roles"].items():
        predicted = [predict(artifact, role, row) for row in fixture["inputs"]]
        mismatches = [i for i, (a, b) in enumerate(zip(predicted, fixture["expected"]))
                      if a != b]
        summary[role] = {"rows": len(predicted), "matches": len(predicted) - len(mismatches),
                         "mismatches": len(mismatches), "first_mismatch_indices": mismatches[:16]}
    matches = sum(x["matches"] for x in summary.values())
    total = sum(x["rows"] for x in summary.values())
    output = {"disposition": "PASS_CONSTRUCTION" if matches == total else "STOP_CONSTRUCTION_PARITY",
              "matches": matches, "total": total, "roles": summary}
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0 if matches == total else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
