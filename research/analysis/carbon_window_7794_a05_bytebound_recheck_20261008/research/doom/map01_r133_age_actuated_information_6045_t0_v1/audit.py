#!/usr/bin/env python3
"""Independent raw-only audit: re-derive each row from the frozen fixture."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
fixture_bytes = (ROOT / "FIXTURE.json").read_bytes()
fixture = json.loads(fixture_bytes)
raw_path = ROOT / "results/t0/RAW.json"
raw_bytes = raw_path.read_bytes()
raw = json.loads(raw_bytes)
assert raw["fixture_sha256"] == hashlib.sha256(fixture_bytes).hexdigest()
assert len(raw["rows"]) == len(fixture["cases"]) == 8
expected = []
for c in fixture["cases"]:
    lineage_ok = c.get("lineage") != "ambiguous" and c["clock"] == "A" and len(c["consumed"]) == 1 and c["effect_obs"] == c["consumed"]
    if not c["intervention_needed"]: status="NOT_APPLICABLE"
    elif c["effect_ms"] is None and c["dispatch_ms"] is None: status="MISS"
    elif c["effect_ms"] is None or c["independent_effect"] is not True or c["effect_relevant"] is not True: status="UNKNOWN"
    elif not lineage_ok: status="UNKNOWN"
    else: status="RELEVANT_EFFECT"
    age=c["effect_ms"]-c["capture_ms"][0] if status=="RELEVANT_EFFECT" else "UNKNOWN"
    latency=c["effect_ms"]-c["dispatch_ms"] if c["effect_ms"] is not None and c["dispatch_ms"] is not None else "UNKNOWN"
    aoi=c["delivery_ms"]-min(c["capture_ms"]) if c["capture_ms"] and c["delivery_ms"] is not None else "UNKNOWN"
    expected.append({"id":c["id"],"delivery_aoi_ms":aoi,"cycle_latency_ms":latency,"effect_age_ms":age,"opportunity_status":status,"credited_relevant_effect":status=="RELEVANT_EFFECT","credited_pulses":0,"intervention_needed":c["intervention_needed"]})
assert raw["rows"] == expected
by={r["id"]:r for r in expected}
assert by["fresh-stalled"]["effect_age_ms"]==1190 and by["older-valid-timely"]["effect_age_ms"]==480
assert by["fresh-stalled"]["cycle_latency_ms"]==1200 and by["older-valid-timely"]["cycle_latency_ms"]==30
assert by["irrelevant-pulses"]["credited_pulses"]==0 and not by["irrelevant-pulses"]["credited_relevant_effect"]
assert by["dispatch-no-effect"]["effect_age_ms"]=="UNKNOWN"
assert by["expired-before-cycle"]["opportunity_status"]=="MISS"
assert by["quiet-no-intervention"]["opportunity_status"]=="NOT_APPLICABLE"
assert by["ambiguous-multi-ancestor"]["effect_age_ms"]=="UNKNOWN"
assert by["cross-clock-unknown"]["effect_age_ms"]=="UNKNOWN"
# Mutation challenges: corrupt lineage, erase the independent effect, or
# make clocks incomparable. The independent oracle must stop crediting age.
mutations_rejected=0
source=fixture["cases"][0]
mutants=(
    {**source,"effect_obs":[999]},
    {**source,"effect_ms":None,"effect_relevant":None,"independent_effect":False},
    {**source,"clock":"incomparable"},
)
for changed in mutants:
    lineage=changed.get("lineage")!="ambiguous" and changed["clock"]=="A" and len(changed["consumed"])==1 and changed["effect_obs"]==changed["consumed"]
    val=changed["effect_ms"]-changed["capture_ms"][0] if changed["effect_ms"] is not None and changed["independent_effect"] and changed["effect_relevant"] is True and lineage else "UNKNOWN"
    if val=="UNKNOWN": mutations_rejected+=1
assert mutations_rejected==3
audit={"status":"METHOD_PASS_SCOPED","rows":8,"independent_oracle_match":8,"mutations_rejected":mutations_rejected,"raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"limits":["synthetic only","no live timing or effect claim","lineage is provided-evidence, not causal proof"]}
out=ROOT/"results/t0/AUDIT.json"
if out.exists(): raise SystemExit("STOP_AUDIT_EXISTS_NO_RETRY")
out.write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
