"""Independent verifier for the redacted A03 evidence package.

It verifies the executed freeze record, retained public inputs/source, and raw
result. It intentionally does not claim byte verification of the withheld
executed candidate, freeze-preparation helper, or original audit script.
"""
import hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
checks=[]
def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8"))

freeze_path=ROOT/"FREEZE.executed.json"
freeze=load(freeze_path)
raw=load(ROOT/"output/raw.json")
redaction=load(ROOT/"PUBLICATION_REDACTION.json")
check("raw.freeze_sha256", raw.get("freeze_sha256")==sha(freeze_path))
check("freeze schema", freeze.get("schema")=="v39-palette-aware-reader-a03-freeze")
check("raw schema", raw.get("schema")=="v39-palette-aware-reader-a03-raw")
check("public retained freeze hashes", True, "per-file checks follow")
withheld={"candidate.py","prepare_freeze.py","audit.py"}
verified=[]
for rel, expected in freeze["files_sha256"].items():
    if rel in withheld: continue
    actual=sha(ROOT/rel)
    check("sha256 "+rel, actual==expected)
    verified.append(rel)
check("withheld helpers explicit", set(redaction.get("withheld_executed_files",[]))==withheld)
check("redacted executed candidate hash recorded", redaction.get("executed_candidate_sha256")==freeze["files_sha256"].get("candidate.py"))
check("executed freeze preparation hash recorded", redaction.get("executed_freeze_preparation_sha256")==freeze["files_sha256"].get("prepare_freeze.py"))
check("public candidate hash", sha(ROOT/redaction["public_candidate_file"])==redaction["public_candidate_sha256"])
check("public candidate identified as non-executed", redaction.get("publication_kind")=="privacy-redacted replay copy; not the executed candidate")
check("redacted source limitation", "not published" in redaction.get("execution_source_limit", ""))
check("wad hash pinned", raw.get("wad_sha256")==freeze.get("wad_sha256"))
check("source hashes pinned", raw.get("source_sha256")==freeze.get("source_sha256"))
images=raw.get("images",[])
check("35 ordered image rows", len(images)==35 and [r.get("sequence") for r in images]==list(range(1,36)))
check("14 palettes per image", all(len(r.get("palette_rows",[]))==14 for r in images))
check("every image uniquely resolved", all(r.get("resolved",{}).get("status")=="observed" and isinstance(r["resolved"].get("palettes"),list) and len(r["resolved"]["palettes"])==1 for r in images))
held=set(freeze.get("heldout_sequences",[]))
heldrows=[r for r in images if r["sequence"] in held]
exact=sum(r["resolved"].get("status")=="observed" and r["recorded_typed"].get("health",{}).get("status")=="observed" and r["recorded_typed"].get("ammo",{}).get("status")=="observed" and r["resolved"].get("value")=={"health":r["recorded_typed"]["health"].get("value"),"ammo":r["recorded_typed"]["ammo"].get("value")} for r in heldrows)
check("heldout set", held==set(list(range(1,31))+list(range(32,35))))
check("33 heldout exact matches", len(heldrows)==33 and exact==33 and raw.get("heldout_exact_matches")==33)
seq31=next((r["resolved"] for r in images if r["sequence"]==31),{})
seq35=next((r["resolved"] for r in images if r["sequence"]==35),{})
check("sequence 31 pair", seq31.get("value")=={"health":97,"ammo":47})
check("sequence 35 pair", seq35.get("value")=={"health":100,"ammo":47})
check("blank no-HUD unknown", raw.get("blank_no_hud_control",{}).get("resolved",{}).get("status")=="unknown")
controls=raw.get("synthetic_controls",{})
check("no common palette unknown", controls.get("no_common_palette",{}).get("resolved",{}).get("status")=="unknown")
check("ambiguous pair unknown", controls.get("ambiguous_pairs",{}).get("resolved",{}).get("status")=="unknown")
check("same pair multiple palettes retained", controls.get("same_pair_multiple_palettes",{}).get("resolved",{}).get("value")=={"health":97,"ammo":47})
check("scope excludes live execution", raw.get("real_game_used") is False and raw.get("real_input_used") is False and raw.get("model_used") is False and raw.get("runtime_modified") is False and raw.get("input_authority_granted") is False)
check("compatibility-only disposition", raw.get("disposition")=="PASS_COMPATIBILITY_ONLY")
result={"schema":"v39-palette-aware-reader-a03-public-audit","status":"PASS" if all(ok for _,ok,_ in checks) else "FAIL","checks_total":len(checks),"checks_passed":sum(ok for _,ok,_ in checks),"retained_frozen_files_verified":len(verified),"withheld_frozen_files":sorted(withheld),"public_candidate_is_executed_source":False,"claim_limit":"This verifies published hashes and recorded compatibility outcomes; it does not byte-verify the withheld executed candidate or prove values against independent HUD truth.","checks":[{"name":n,"passed":ok,"detail":d} for n,ok,d in checks]}
(ROOT/"PUBLIC_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":result["status"],"checks_total":len(checks),"checks_passed":result["checks_passed"],"verified_files":len(verified)}))
sys.exit(0 if result["status"]=="PASS" else 1)
