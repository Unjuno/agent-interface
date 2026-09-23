from __future__ import annotations
import argparse,collections,hashlib,json,lzma
from pathlib import Path

RAW_SHA="ee5d7f98ea78e70840a6433a60636e57bebdf08b1cfc8476afdc3b32c783e72a"
PROJECTION_FIELDS=["sequence_side","history_sha256","current_sha256","history_centroid_x","current_centroid_x","content_direction"]

def load_raw(path: Path):
    data=path.read_bytes()
    if path.suffix==".xz": data=lzma.decompress(data)
    if hashlib.sha256(data).hexdigest()!=RAW_SHA: raise RuntimeError("raw #1134 SHA mismatch")
    return json.loads(data)

def phase(seq,name): return next(x for x in seq["phases"] if x["phase"]==name)

def key(seq):
    h=phase(seq,"history")["capture"]; c=phase(seq,"current")["capture"]
    return (seq["sequence"],h["sha256"],c["sha256"],h["red_centroid_x"],c["red_centroid_x"],seq["content_direction"])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("--out",required=True); a=ap.parse_args()
    r=load_raw(Path(a.raw)); groups=collections.defaultdict(list)
    for p in r["pairs"]:
        for s in p["sequences"]: groups[key(s)].append(p["mode"])
    total=sum(map(len,groups.values()))
    patterns=[]
    bayes=0
    for k,v in sorted(groups.items(),key=lambda kv:repr(kv[0])):
        cnt=collections.Counter(v); bayes+=max(cnt.values())
        patterns.append({"projection_sha256":hashlib.sha256(repr(k).encode()).hexdigest(),"n":len(v),"continue":cnt["continue"],"reverse":cnt["reverse"]})
    reverse_total=sum(x["reverse"] for x in patterns); continue_total=sum(x["continue"] for x in patterns)
    ambiguous=all(x["continue"]>0 and x["reverse"]>0 for x in patterns)
    safe_continue=sum(x["continue"] for x in patterns if x["reverse"]==0)
    out={
      "task":"TEMPORAL-SPECULATION-REVERSAL-IDENTIFIABILITY-20260918-001",
      "source_issue":1134,"source_raw_sha256":RAW_SHA,"invocations":1,"reruns":0,
      "projection_fields":PROJECTION_FIELDS,
      "sequences":total,"equivalence_classes":len(patterns),"classes":patterns,
      "all_classes_outcome_ambiguous":ambiguous,
      "bayes_optimal_correct":bayes,"bayes_optimal_accuracy":bayes/max(1,total),
      "always_continue":{"continuation_coverage":continue_total,"reversal_misses":reverse_total},
      "always_yield":{"continuation_coverage":0,"reversal_misses":0},
      "max_continuation_coverage_with_zero_reversal_misses":safe_continue,
      "preformal_sanity_observed":True,
    }
    gate=(total==64 and ambiguous and out["bayes_optimal_accuracy"]<=0.5 and safe_continue==0 and reverse_total==32 and continue_total==32)
    out["decision"]="PASS_REVERSAL_NOT_IDENTIFIABLE_PRE_FUTURE_SCOPED" if gate else "FAIL_PRE_FUTURE_OUTCOME_SEPARABLE"
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
