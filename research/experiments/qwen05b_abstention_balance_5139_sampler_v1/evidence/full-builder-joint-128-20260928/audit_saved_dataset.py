import json
import sys
from pathlib import Path
from independent_audit import audit_document
source=Path(sys.argv[1])
document=json.loads(source.read_text(encoding="utf-8"))
errors=audit_document(document)
print(json.dumps({"verdict":"PASS_FULL_BUILDER_JOINT_RAW_AUDIT" if not errors else "FAIL_FULL_BUILDER_JOINT_RAW_AUDIT","errors":errors,"raw_bytes":source.stat().st_size},sort_keys=True))
raise SystemExit(0 if not errors else 2)

