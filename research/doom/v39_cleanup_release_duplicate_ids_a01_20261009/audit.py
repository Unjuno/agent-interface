import hashlib,json,sys
EXPECTED_SOURCE="bc8d3550e6c2d057c7b615b38e424de3497418547e835490429f526853e1fe28"
EXPECTED={"single_matching_token":(True,True),"single_legacy_tokenless_terminal":(True,True),"single_mismatched_token":(True,False),"missing_terminal":(False,False),"duplicate_accept_unreleased_first":(False,False),"duplicate_terminals_matching_last":(False,False),"duplicate_terminals_mismatching_last":(False,False)}
def audit(raw):
 digest=hashlib.sha256(raw).hexdigest();d=json.loads(raw)
 if d.get("schema")!="issue59-cleanup-duplicate-id-candidate-v1" or d.get("pinned_source_sha256")!=EXPECTED_SOURCE:raise ValueError("schema/source")
 if d.get("candidate_invocations")!=1 or d.get("runtime_invocations")!=0:raise ValueError("scope/count")
 rows=d.get("rows")
 if type(rows)is not list or len(rows)!=len(EXPECTED):raise ValueError("coverage")
 got={}
 for r in rows:
  k=r.get("case_id")
  if k not in EXPECTED or k in got:raise ValueError("case identity")
  got[k]=(r.get("input_terminals_complete"),r.get("input_releases_verified_empty"))
 if set(got)!=set(EXPECTED):raise ValueError("missing case")
 out=[{"case_id":k,"expected":list(v),"observed":list(got[k]),"matches_gate":got[k]==v} for k,v in EXPECTED.items()]
 dup=[r for r in out if r["case_id"].startswith("duplicate_")]
 passed=all(r["matches_gate"] for r in out)
 return {"auditor_invocations":1,"input_sha256":digest,"cases_checked":len(out),"controls_match":all(r["matches_gate"] for r in out if not r["case_id"].startswith("duplicate_")),"ambiguous_duplicates_rejected":all(r["matches_gate"] for r in dup),"duplicate_terminal_order_dependent":got["duplicate_terminals_matching_last"]!=got["duplicate_terminals_mismatching_last"],"decision":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD","cases":out,"scope":"Synthetic cleanup receipt reconstruction only; no live process, input, physical release, GUI, game, model, survival, or product inference."}
if __name__=="__main__": print(json.dumps(audit(sys.stdin.buffer.read()),sort_keys=True,separators=(",",":")))
