from __future__ import annotations
import argparse, hashlib, json, math, random
from pathlib import Path

N=1024
SHIFT=512
WINDOW=64
ALARM_K=6
HORIZON=16
REFERENCE_P99=-math.log(0.01)
DETERMINISTIC_CUTOFF=8.0
CONDITIONS=("stationary","declared_shift","undeclared_shift")
FORMAL_SEEDS=tuple(range(65764101,65764131))


def exp_sample(rng: random.Random, scale: float=1.0) -> float:
    u=max(rng.random(),1e-15)
    return -math.log(u)*scale


def generate(seed: int, condition: str):
    if type(seed) is not int or condition not in CONDITIONS:
        raise ValueError("invalid input")
    rng=random.Random(seed)
    samples=[]; modes=[]
    for i in range(N):
        shifted=i>=SHIFT and condition in {"declared_shift","undeclared_shift"}
        if shifted and rng.random()<0.10:
            value=8.0+exp_sample(rng,4.0)
        else:
            value=exp_sample(rng,1.0)
        samples.append(value)
        modes.append("rare_heavy" if condition=="declared_shift" and i>=SHIFT else "reference")
    return samples,modes


def sample_alarm_index(samples):
    flags=[v>REFERENCE_P99 for v in samples]
    count=sum(flags[:WINDOW])
    if count>=ALARM_K:
        return WINDOW-1
    for end in range(WINDOW,len(samples)):
        count += int(flags[end])-int(flags[end-WINDOW])
        if count>=ALARM_K:
            return end
    return None


def declared_mode_index(modes):
    return next((i for i,m in enumerate(modes) if m!="reference"),None)


def first_extreme_in_horizon(samples):
    return next((i for i in range(SHIFT,min(SHIFT+HORIZON,len(samples))) if samples[i]>REFERENCE_P99),None)


def row(seed,condition):
    samples,modes=generate(seed,condition)
    sample_alarm=sample_alarm_index(samples)
    mode_alarm=declared_mode_index(modes)
    digest=hashlib.sha256(json.dumps(samples,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return {
      "seed":seed,"condition":condition,"n":N,"shift_index":SHIFT,
      "reference_p99":REFERENCE_P99,"window":WINDOW,"alarm_k":ALARM_K,"horizon":HORIZON,
      "sample_alarm_index":sample_alarm,"declared_mode_invalidation_index":mode_alarm,
      "static_reference_invalidation_index":None,
      "first_extreme_in_horizon":first_extreme_in_horizon(samples),
      "deterministic_cutoff":DETERMINISTIC_CUTOFF,
      "cutoff_exceedances_in_horizon":sum(v>DETERMINISTIC_CUTOFF for v in samples[SHIFT:SHIFT+HORIZON]),
      "sample_sha256":digest,"samples":samples,"modes":modes,
      "authority":False,"task_success":None,
    }


def decide(rows):
    stationary=[r for r in rows if r["condition"]=="stationary"]
    declared=[r for r in rows if r["condition"]=="declared_shift"]
    undeclared=[r for r in rows if r["condition"]=="undeclared_shift"]
    stationary_false=sum(r["sample_alarm_index"] is not None for r in stationary)
    metadata_exact=all(r["declared_mode_invalidation_index"]==SHIFT for r in declared)
    metadata_noinvent=all(r["declared_mode_invalidation_index"] is None for r in stationary+undeclared)
    counterexamples=[r for r in declared if r["sample_alarm_index"] is not None and r["sample_alarm_index"]-SHIFT>HORIZON and r["first_extreme_in_horizon"] is not None]
    complete=(len(stationary),len(declared),len(undeclared))==(30,30,30)
    passed=complete and stationary_false<=1 and metadata_exact and metadata_noinvent and bool(counterexamples)
    return {
      "decision":"PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED" if passed else "FAIL_OR_HOLD_A04_GATE",
      "rows":len(rows),"stationary_sample_false_alarms":stationary_false,
      "metadata_exact_declared":metadata_exact,"metadata_no_invention":metadata_noinvent,
      "counterexample_count":len(counterexamples),
      "counterexample_seeds":[r["seed"] for r in counterexamples],
      "formal_invocations":1,"reruns":0,"authority":False,"task_success":None,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    rows=[]
    with (out/"RAW.jsonl").open("w",encoding="utf-8") as f:
        for condition in CONDITIONS:
            for seed in FORMAL_SEEDS:
                r=row(seed,condition); rows.append(r); f.write(json.dumps(r,separators=(",",":"),allow_nan=False)+"
")
    result=decide(rows)
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"
",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
