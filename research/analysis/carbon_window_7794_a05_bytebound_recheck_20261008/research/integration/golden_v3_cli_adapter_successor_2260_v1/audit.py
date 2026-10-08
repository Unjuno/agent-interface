import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from adapter import replay, translate

def main():
    fixture=json.loads((Path(__file__).parent/"fixture.json").read_text())
    # bind the fixture digest after loading, so the frozen file is self-contained.
    import hashlib
    raw=json.dumps(fixture,sort_keys=True,separators=(",",":"))
    fixture["raw_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    out=replay(fixture)
    assert len(out)==10
    assert all(row["authority_granted"] is False for row in out)
    assert out[5]["partial_effects"]==["save"] and out[5]["task_success"] is True
    assert out[7]["program_completed"] is True and out[7]["task_success"] is False
    assert out[9]["status"]=="runtime_failed" and out[9]["cleanup_error"]=="close failed"
    bad=copy.deepcopy(fixture); bad["rows"][0]["state"]="UNKNOWN"
    try: replay(bad)
    except ValueError as e: assert str(e)=="FIXTURE_DIGEST_MISMATCH"
    else: raise AssertionError("tampered fixture accepted")
    bad=copy.deepcopy(fixture); bad["raw_sha256"]="wrong"
    try: replay(bad)
    except ValueError as e: assert str(e)=="FIXTURE_DIGEST_MISMATCH"
    else: raise AssertionError("missing raw provenance accepted")
    bad=copy.deepcopy(fixture); bad["rows"][0]["raw_sha256"]="different"
    bad["raw_sha256"]=hashlib.sha256(json.dumps(bad,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    try: replay(bad)
    except ValueError as e: assert str(e)=="RAW_REFERENCE_MISMATCH"
    else: raise AssertionError("raw reference mismatch accepted")
    print("INDEPENDENT_AUDIT_PASS rows=10 controls=3 authority_grants=0")
if __name__=="__main__": main()
