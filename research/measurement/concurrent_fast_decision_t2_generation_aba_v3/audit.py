import argparse, json, random
SEED=145920260918012
CLASSES=["ABA_CLEAR","ABA_BOUNCE","FRESH_G2","WATCH","HARD","AUTH_FALSE","REPLAY","CROSS_SCOPE","FORGED_GEN","DUP_RETURN"]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True); a=ap.parse_args()
 data=json.load(open(a.result,encoding="utf-8")); rows=data["rows"]; s=data["summary"]; errors=[]
 if len(rows)!=200000: errors.append("row_count")
 exp=[]
 for k in CLASSES: exp.extend([k]*20000)
 random.Random(SEED).shuffle(exp)
 if [r["class"] for r in rows]!=exp: errors.append("schedule")
 if any(r["i"]!=i for i,r in enumerate(rows)): errors.append("indices")
 if any(r["mismatch"] for r in rows): errors.append("candidate_oracle")
 aba=[r for r in rows if r["class"] in ("ABA_CLEAR","ABA_BOUNCE")]
 if len(aba)!=40000 or any(r["stale_candidate"] for r in aba): errors.append("aba_escape")
 if sum(r["stale_comparator"] for r in aba)!=40000: errors.append("discriminator")
 if sum(r["fresh_effect"] for r in rows if r["class"]=="FRESH_G2")!=20000: errors.append("fresh_overinvalidated")
 if any(r["fresh_effect"] for r in rows if r["class"] in ("WATCH","HARD","AUTH_FALSE")): errors.append("bad_effect")
 if s.get("decision")!="PASS_T2_GENERATION_ABA_GUARD_SCOPED": errors.append("decision")
 out={"decision":"PASS_AUDIT" if not errors else "FAIL_AUDIT","errors":errors,"rows":len(rows),"aba":len(aba),"comparator_stale_effects":sum(r["stale_comparator"] for r in aba)}
 json.dump(out,open(a.out,"w",encoding="utf-8"),sort_keys=True,indent=2); print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
