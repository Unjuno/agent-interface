"""Independent construction auditor; does not import the trainer or loader."""
import hashlib
import json
from pathlib import Path

import torch
import torch.nn.functional as F

ARMS = ("control16", "treatment64")
ROLES = ("A", "B", "C")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def predict(artifact, role, rows):
    state = artifact["tensors"][role]
    t = lambda key: torch.tensor(state[key], dtype=torch.float32)
    x = torch.tensor(rows, dtype=torch.float32)
    if role == "A":
        h = torch.tanh(F.linear(x, t("enc.0.weight"), t("enc.0.bias")))
        logits = F.linear(h, t("head.weight"), t("head.bias"))
    else:
        h = torch.tanh(F.linear(x, t("core.enc.0.weight"), t("core.enc.0.bias")))
        logits = F.linear(h, t("core.head.weight"), t("core.head.bias")) + h @ t("a") @ t("b") / 2
    return logits.argmax(-1).tolist()


def main(root):
    root = Path(root)
    reports = {}
    for arm in ARMS:
        d = root / arm
        artifact = json.loads((d / "skill.json").read_text(encoding="utf-8"))
        expected = json.loads((d / "expected.json").read_text(encoding="utf-8"))
        raw = json.loads((d / "skill.json").read_text(encoding="utf-8"))
        digest = raw.pop("payload_sha256")
        assert digest == hashlib.sha256(canonical(raw)).hexdigest(), "payload_digest"
        assert artifact["provenance"]["allocation"] == "needle-role-skill-c-support64-4749-v1"
        assert artifact["provenance"]["role_c_support_rows"] == expected["role_c_support_rows"]
        assert expected["base_immutable"] is True and expected["support16_prefix_of_64"] is True
        assert expected["arm"] == arm
        roles = {}
        for role in ROLES:
            observed = expected["roles"][role]
            recomputed = predict(artifact, role, observed["inputs"])
            assert recomputed == observed["pred"], f"{arm}_{role}_prediction"
            accuracy = sum(x == y for x, y in zip(recomputed, observed["expected"])) / len(recomputed)
            loader_results = []
            for loader in ("load1", "load2"):
                result = json.loads((d / loader / "loader.json").read_text(encoding="utf-8"))
                assert result["accepted"] is True and result["artifact_sha256"] == hashlib.sha256((d / "skill.json").read_bytes()).hexdigest()
                assert result["predictions"] == {r: expected["roles"][r]["pred"] for r in ROLES}
                expected_controls = {"tampered_digest": "YIELD", "wrong_adapter_version": "YIELD",
                                     "skipped_edge": "YIELD", "wrong_scope": "YIELD",
                                     "unverified_outcome": "YIELD", "unknown_destination": "YIELD",
                                     "truncated": "YIELD", "unknown_schema": "YIELD",
                                     "duplicate_receipt": "ADVANCE", "duplicate_receipt_second": "YIELD"}
                assert len(result["graphs"]) == 2 and all(
                    g["flow"] == ["ADVANCE", "ADVANCE"] and g["old_receipt"] == "YIELD" and
                    g["controls"] == expected_controls and g["fixture_emissions"] == 2
                    for g in result["graphs"])
                loader_results.append(True)
            roles[role] = {"accuracy": accuracy, "rows": len(recomputed), "two_loaders_exact": all(loader_results)}
        reports[arm] = {"payload_sha256": digest, "roles": roles}
    for role in ("A", "B"):
        assert reports["control16"]["roles"][role]["accuracy"] == reports["treatment64"]["roles"][role]["accuracy"]
    report = {"schema": "needle-role-skill-c-support64-construction-audit-v1",
              "status": "CONSTRUCTION_AUDIT_PASS", "seed": 7865001,
              "arms": reports, "errors": [],
              "scope": "one synthetic local-Docker construction seed only; no formal inference"}
    (root / "construction-audit.json").write_bytes(canonical(report) + b"\n")
    print(json.dumps({"status": report["status"], "seed": report["seed"],
                      "accuracies": {arm: {r: x["accuracy"] for r, x in item["roles"].items()}
                                     for arm, item in reports.items()}}, sort_keys=True))


if __name__ == "__main__":
    import sys
    torch.set_num_threads(1)
    main(sys.argv[1])
