from __future__ import annotations
import argparse,collections,hashlib,json,lzma
from pathlib import Path
RAW_SHA="ee5d7f98ea78e70840a6433a60636e57bebdf08b1cfc8476afdc3b32c783e72a"
EXPECTED=["sequence_side","history_sha256","current_sha256","history_centroid_x","current_centroid_x","content_direction"]
BANNED={"mode","future","future_sha256","future_label","authored","content_reversal","content_future_direction","content_future_label"}

def phase(s,n): return next(x for x in s["phases"] if x["phase"]==n)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("raw");ap.add_argument("result");ap.add_argument("--out",required=True);a=ap.parse_args()
 data=Path(a.raw).read_bytes(); data=lzma.decompress(data) if Path(a.raw).suffix==".xz" else data
 errors=[]
 if hashlib.sha256(data).hexdigest()!=RAW_SHA: errors.append("raw_sha")
 raw=json.loads(data); got=json.loads(Path(a.result).read_text())
 if got.get("projection_fields")!=EXPECTED: errors.append("projection_contract")
 if BANNED.intersection(got.get("projection_fields",[])): errors.append("future_leakage")
 groups=collections.defaultdict(list)
 for p in raw["pairs"]:
  for s in p["sequences"]:
   h=phase(s,"history")["capture"];c=phase(s,"current")["capture"]
   k=(s["sequence"],h["sha256"],c["sha256"],h["red_centroid_x"],c["red_centroid_x"],s["content_direction"])
   groups[k].append(p["mode"])
 total=sum(map(len,groups.values())); bayes=sum(max(collections.Counter(v).values()) for v in groups.values())
 safe=sum(collections.Counter(v)["continue"] for v in groups.values() if collections.Counter(v)["reverse"]==0)
 recomputed=(total,len(groups),bayes/total,safe,all(set(v)=={"continue","reverse"} for v in groups.values()))
 claimed=(got.get("sequences"),got.get("equivalence_classes"),got.get("bayes_optimal_accuracy"),got.get("max_continuation_coverage_with_zero_reversal_misses"),got.get("all_classes_outcome_ambiguous"))
 if recomputed!=claimed: errors.append("recompute")
 # Leakage mutation control: adding outcome/mode must make the projection contract invalid.
 mutated=EXPECTED+["mode"]
 if not BANNED.intersection(mutated): errors.append("leakage_control")
 expected_dec="PASS_REVERSAL_NOT_IDENTIFIABLE_PRE_FUTURE_SCOPED" if (total==64 and len(groups)==2 and bayes/total<=.5 and safe==0 and all(set(v)=={"continue","reverse"} for v in groups.values())) else "FAIL_PRE_FUTURE_OUTCOME_SEPARABLE"
 if got.get("decision")!=expected_dec: errors.append("decision")
 out={"passed":not errors,"errors":errors,"decision":got.get("decision"),"raw_sha256":RAW_SHA,"recomputed":{"sequences":total,"classes":len(groups),"bayes_accuracy":bayes/total,"safe_continue_coverage":safe},"leakage_mutation_rejected":bool(BANNED.intersection(mutated))}
 Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
