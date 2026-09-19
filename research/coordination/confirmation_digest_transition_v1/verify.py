import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


unbound = load("canonical_unbound.json")
unbound_confirmation = load("confirm_unbound.json")
changed = load("canonical_bound_changed.json")
revision = load("canonical_bound_revision.json")
stable = load("canonical_bound_stable.json")
result = load("result.json")

assert unbound["active_generation"] == 2
assert unbound_confirmation["revision"] == 2
assert unbound_confirmation["receipts"][1]["status"] == "UNKNOWN"

assert changed["active_generation"] == 1
assert changed["confirmation_revision"] == 2
assert changed["confirmation_content_id"] == "5eceb2d5b5af55fcc94d09d4c745ffb5ee40f05fd114352444a96714c7194dd8"

assert revision["active_generation"] == 1
assert revision["confirmation_revision"] == 2
assert revision["confirmation_content_id"] == "51ea2d31c0b555b2aad8587f3e78201bd28ab1e41c3850a93824dbfe89e95b90"

assert stable["active_generation"] == 2
assert stable["confirmation_revision"] == 1

assert result["decision"] == "PASS_CONFIRMATION_IDENTITY_BOUND_CANONICAL_CAS_SCOPED"
assert result["totals"]["old_decision_generation_successes"] == 1
assert result["totals"]["candidate_stale_sha_409s"] == 2
assert result["totals"]["fresh_sha_retries_after_stale_decision"] == 0
print("PASS_CONFIRMATION_IDENTITY_BOUND_CANONICAL_CAS_SCOPED")
