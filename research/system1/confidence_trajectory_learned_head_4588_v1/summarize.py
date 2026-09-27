"""Read-only post-run aggregation; does not train or edit formal evidence."""
import argparse
import json
import math
from pathlib import Path

ARMS=["CURRENT_ONLY","LEVEL_VELOCITY","LEVEL_VELOCITY_ACCEL","CAUSAL_SMOOTHED"]


def quantile(xs,q):
    ys=sorted(xs)
    return ys[max(0,math.ceil(q*len(ys))-1)]


def main():
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();root=Path(a.root)
    audit=json.loads((root/"audit/AUDIT.json").read_text(encoding="utf-8"))
    formal=json.loads((root/"FORMAL_ORCHESTRATION.json").read_text(encoding="utf-8"))
    all_lat={arm:[] for arm in ARMS};state_sizes={arm:[] for arm in ARMS};train_ms={arm:[] for arm in ARMS}
    for seed in audit["per_seed"]:
        doc=json.loads((root/f"training/seed-{seed['seed']}"/"evidence.json").read_text(encoding="utf-8"))
        for arm in ARMS:
            rec=doc["arms"][arm]
            all_lat[arm].extend(rec["decision_latency_ms"])
            state_sizes[arm].append(rec["state_bytes"])
            train_ms[arm].append(rec["elapsed_train_ms"])
    latency={arm:{"samples":len(xs),"p50_ms":quantile(xs,.5),"p95_ms":quantile(xs,.95),
                  "max_ms":max(xs)} for arm,xs in all_lat.items()}
    summary={"schema":"confidence-trajectory-post-run-summary-v1",
             "status":"HOLD_NOISE_AMPLIFICATION" if not all(audit["gates"].values()) and not audit["error_count"] else audit["status"],
             "formal_status":formal["status"],"formal_orchestrations":formal["formal_orchestrations"],
             "retries":formal["retries"],"runner_rc":formal["runner"]["returncode"],
             "auditor_rc":formal["auditor"]["returncode"],"audit_status":audit["status"],
             "audit_errors":audit["error_count"],"gates":audit["gates"],"pooled":audit["pooled"],
             "latency":latency,
             "state_bytes_mean":{arm:sum(v)/len(v) for arm,v in state_sizes.items()},
             "training_ms_sum_by_arm":{arm:sum(v) for arm,v in train_ms.items()},
             "seeds":10,"test_rows":audit["pooled"]["CURRENT_ONLY"]["overall"]["rows"],
             "accuracy_cells":len(ARMS)*len(audit["per_seed"]),
             "image_id":formal["image_id"],"freeze_sha256":formal["freeze_sha256"]}
    path=root/"POST_RUN_SUMMARY.json"
    path.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"status":summary["status"],"gates":summary["gates"],"pooled":summary["pooled"],
                      "latency":latency,"summary":str(path)},sort_keys=True))


if __name__=="__main__":main()
