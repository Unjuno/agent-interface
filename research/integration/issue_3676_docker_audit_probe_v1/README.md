Issue #3676 local Docker audit reproduction

H: The frozen #3675 audit accepts contradictory/non-canonical event traces and its documented CLI invocation fails.
T: Preserve #3675 raw/freeze/audit/source unchanged. Run frozen auditor in local Docker, network-disabled with read-only frozen inputs. Probe unexpected event, duplicate stale row, contradictory bridge flags, reordered transitions and unsupported field; invoke documented CLI shape once.
D: Record hashes, baseline, each mutation and CLI status. This reproduces the defect; it does not implement a hardened auditor.
C: Docker Desktop 4.91.0 / Engine 29.8.0, python:3.12-slim, linux/amd64, network none, read-only inputs. No GUI/X11/model/input; no retry.
U: Five finite controls do not characterize every weakness or alter original X11 result.

Result: FAIL_AUDIT_CONTRADICTORY_MUTATIONS_ACCEPTED; STOP_CLI_USAGE_ERROR. See evidence/result.json. Frozen original bytes and Docker replay inputs are included here. No formal X11 rerun.
