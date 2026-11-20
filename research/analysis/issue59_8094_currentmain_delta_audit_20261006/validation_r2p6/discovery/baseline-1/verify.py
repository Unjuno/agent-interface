#!/usr/bin/env python3
import json
from pathlib import Path

data=json.loads((Path(__file__).with_name("RESULT.json")).read_text())
assert data["decision"]=="PASS_CURRENT_MAIN_DELTA_NONCONFLICT_SCOPED"
assert data["counts"]=={"total":11,"clean_add":3,"main_unchanged_candidate_only":8,"conflicts":0}
assert len(data["paths"])==11
for row in data["paths"]:
    if row["classification"]=="CANDIDATE_ADD_CLEAN":
        assert row["base_sha"] is None and row["main_sha"] is None and row["candidate_sha"]
    elif row["classification"]=="MAIN_UNCHANGED_CANDIDATE_ONLY":
        assert row["base_sha"]==row["main_sha"] and row["candidate_sha"]!=row["main_sha"]
    else:
        raise AssertionError(row)
print("PASS 11 paths: 3 clean additions, 8 main-unchanged candidate edits, 0 conflicts")
