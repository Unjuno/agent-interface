Issue #3676 local Docker audit reproduction

H: The frozen #3675 audit accepts contradictory/non-canonical event traces and its documented CLI invocation fails.
T: Preserve #3675 raw/freeze/audit/source unchanged. Run frozen auditor in local Docker, network-disabled with read-only frozen inputs. Probe unexpected event, duplicate stale row, contradictory bridge flags, reordered transitions and unsupported field; invoke documented CLI shape once.
D: Record hashes, baseline, each mutation and CLI status. This reproduces the defect; it does not implement a hardened auditor.
C: Docker Desktop 4.91.0 / Engine 29.8.0, python:3.12-slim, linux/amd64, network none, read-only inputs. No GUI/X11/model/input; no retry.
U: Five finite controls do not characterize every weakness or alter original X11 result.

Historical result: `FAIL_AUDIT_CONTRADICTORY_MUTATIONS_ACCEPTED` and `STOP_CLI_USAGE_ERROR`, preserved unchanged in `evidence/result.json`. The first Docker workflow also returned red because its assertion incorrectly required every mutation to be rejected, even though this probe's hypothesis is that five specified mutations are accepted.

The corrected `reproduce.py` is a validation of that finite finding, not a hardened-auditor PASS. Its acceptance gate pins all four frozen hashes, requires the baseline to pass, requires exactly the five documented mutations to be accepted and four controls to be rejected, and confirms the same CLI usage failure. A green `frozen-audit-probe` job therefore means **the recorded auditor weaknesses reproduced exactly** (`PASS_REPRODUCED_FROZEN_AUDIT_WEAKNESSES`); it does not mean the frozen auditor is sound. The original red workflow run and historical JSON remain in PR/Actions history. No formal X11 rerun.
