import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
assert r["decision"]=="PASS_CROSS_FILE_TOCTOU_BOUNDARY_SCOPED"
assert r["split_stable"]["advance"] is True
assert r["split_stable"]["final"]=={"membership_epoch":1,"members":["A","B"],"active_generation":2}
assert r["split_race"]["stale_membership_authorized_advance"] is True
assert r["split_race"]["final"]=={"membership_epoch":2,"members":["A","B","C"],"active_generation":2}
assert r["unified_race"]["stale_generation_attempt_status"]==409
assert r["unified_race"]["stale_write_rejected"] is True
assert r["unified_race"]["final"]=={"membership_epoch":2,"members":["A","B","C"],"active_generation":1}
print("PASS_VERIFY")
