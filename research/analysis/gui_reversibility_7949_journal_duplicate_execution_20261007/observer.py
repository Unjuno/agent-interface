import json
import sqlite3
import sys

db_path, case_id = sys.argv[1:3]
db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
state = db.execute("SELECT revision, agent_value, external_value FROM artifact WHERE id=1").fetchone()
cert = db.execute("SELECT base_revision, agent_field, agent_original, baseline_state FROM recovery_certificate WHERE id=1").fetchone()
journal = db.execute("SELECT seq, revision, field, before_value, after_value FROM journal ORDER BY seq").fetchall()
db.close()
snapshot = {"case_id": case_id, "state": dict(zip(("revision","agent_value","external_value"), state)),
            "certificate": {"base_revision": cert[0], "agent_field": cert[1], "agent_original": cert[2], "baseline_state": json.loads(cert[3])},
            "journal": [dict(zip(("seq","revision","field","before_value","after_value"), row)) for row in journal]}
print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))
