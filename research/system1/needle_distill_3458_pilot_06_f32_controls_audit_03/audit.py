"""Float32-aware invalid-control wrapper around the frozen full auditor."""
import copy
import importlib.util
import json
import math
from pathlib import Path

PRIOR_PATH = (Path(__file__).resolve().parent.parent /
              "needle_distill_3458_pilot_06_corrected_covariate_audit_02" / "audit.py")
_spec = importlib.util.spec_from_file_location("frozen_covariate_audit_3899", PRIOR_PATH)
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)

EXPECTED = [
    ("stale_epoch", prior.META | {"epoch": 8}, [.2,.2,0.,0.,.9,1.], "YIELD_METADATA"),
    ("wrong_scope", prior.META | {"scope": "other"}, [.2,.2,0.,0.,.9,1.], "YIELD_METADATA"),
    ("wrong_intent", {"intent":"other","scope":prior.META["scope"],"epoch":prior.META["epoch"]}, [.2,.2,0.,0.,.9,1.], "YIELD_METADATA"),
    ("out_of_envelope", prior.META, [1.3,0.,0.,0.,.9,1.], "YIELD_ENVELOPE"),
    ("nonfinite", prior.META, ["NaN",0.,0.,0.,.9,1.], "YIELD_NONFINITE"),
]
TOLERANCE = 1e-6


def validate_invalid(records):
    errors=[]
    if [r.get("seed") for r in records] != list(prior.SEEDS):
        return ["invalid_seed_set"], 0
    count=0
    for record,seed in zip(records,prior.SEEDS):
        controls=record.get("invalid_controls",[])
        if len(controls)!=len(EXPECTED):
            errors.append(f"seed_{seed}:invalid_count")
            continue
        for actual,(case,meta,expected_x,reason) in zip(controls,EXPECTED):
            prefix=f"seed_{seed}:invalid:{case}"
            if actual.get("case")!=case or actual.get("meta")!=meta:
                errors.append(prefix+":identity")
            if actual.get("reason")!=reason or actual.get("proposal") is not None:
                errors.append(prefix+":decision")
            got=actual.get("x",[])
            if not isinstance(got,list) or len(got)!=6:
                errors.append(prefix+":width")
                continue
            valid=True
            for i,(observed,want) in enumerate(zip(got,expected_x)):
                if want=="NaN":
                    if observed!="NaN":
                        errors.append(prefix+f":feature_{i}_nan_encoding")
                        valid=False
                else:
                    try:
                        value=float(observed)
                        if not math.isfinite(value) or abs(value-float(want))>TOLERANCE:
                            errors.append(prefix+f":feature_{i}_mismatch")
                            valid=False
                    except (TypeError,ValueError):
                        errors.append(prefix+f":feature_{i}_type")
                        valid=False
            if valid:
                # The frozen predecessor auditor expects decimal literals exactly.
                # Normalize only this deep copy after our float32-tolerant check;
                # raw bytes remain separately bound and are passed unchanged.
                actual["x"]=expected_x.copy()
                count+=1
    return errors,count


def audit(payload,raw):
    cloned=copy.deepcopy(payload)
    errors,count=validate_invalid(cloned.get("seeds",[]))
    result=prior.audit(cloned,raw)
    merged=errors+result.get("errors",[])
    result["errors"]=merged
    result["audit"]="PASS" if not merged else "FAIL"
    result["invalid_float32_controls_tolerance"]=TOLERANCE
    result["invalid_float32_controls_validated"]=count
    result["invalid_controls_normalized_only_after_validation"]=True
    result["prior_auditor_commit"]="e978a33473d7d2536d43cf68ffcb16e344e4b6d8"
    return result


def self_test():
    for case,meta,expected_x,reason in EXPECTED:
        actual_x=[float(v) if v!="NaN" else "NaN" for v in expected_x]
        # Match how torch.float32 -> Python float serializes decimal inputs.
        import struct
        actual_x=[struct.unpack("f",struct.pack("f",v))[0] if isinstance(v,float) else v for v in actual_x]
        sample={"seed":prior.SEEDS[0],"invalid_controls":[{"case":c,"meta":m,"reason":r,"proposal":None,"x":x} for c,m,x,r in EXPECTED]}
        sample["invalid_controls"][EXPECTED.index((case,meta,expected_x,reason))]["x"]=actual_x
        errors,count=validate_invalid([sample]+[
            {"seed":s,"invalid_controls":[{"case":c,"meta":m,"reason":r,"proposal":None,"x":[float(v) if v!="NaN" else "NaN" for v in x]} for c,m,x,r in EXPECTED]}
            for s in prior.SEEDS[1:]])
        assert errors==[],errors
        assert count==15,count
        break
    # Changes beyond tolerance are rejected; NaN encoding is exact.
    sample={"seed":prior.SEEDS[0],"invalid_controls":[{"case":c,"meta":m,"reason":r,"proposal":None,"x":[float(v) if v!="NaN" else "NaN" for v in x]} for c,m,x,r in EXPECTED]}
    sample["invalid_controls"][0]["x"][0]+=.001
    bad=[sample]+[{"seed":s,"invalid_controls":[{"case":c,"meta":m,"reason":r,"proposal":None,"x":[float(v) if v!="NaN" else "NaN" for v in x]} for c,m,x,r in EXPECTED]} for s in prior.SEEDS[1:]]
    errors,_=validate_invalid(bad)
    assert "seed_3467:invalid:stale_epoch:feature_0_mismatch" in errors
    print(json.dumps({"construction":"PASS","float32_controls_accepted":15,"beyond_tolerance_rejected":True,"nan_encoding_exact":True},sort_keys=True))


if __name__=="__main__":
    import sys
    if "--self-test" in sys.argv:
        self_test(); raise SystemExit(0)
    source=Path(sys.argv[1]); raw=source.read_bytes(); payload=json.loads(raw.decode("utf-8"))
    result=audit(payload,raw)
    encoded=(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n").encode()
    if "--output" in sys.argv:
        target=Path(sys.argv[sys.argv.index("--output")+1])
        with target.open("xb") as stream: stream.write(encoded)
    sys.stdout.buffer.write(encoded)
    if result["audit"]!="PASS": raise SystemExit(2)
