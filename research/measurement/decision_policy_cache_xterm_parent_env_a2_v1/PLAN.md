# #1359 XTerm parent-environment successor

H/T/D/C/U and all scientific thresholds remain exactly Issue #1349.

Only harness repair: scope the parent Python process DISPLAY/XAUTHORITY to the fresh private-Xvfb values for each case before parent Python-Xlib Display() creation, then restore the exact prior values after case cleanup. Child XTerm env is unchanged. No renderer/ROI/policy/timing/effect/scorer threshold change.

Canonical parent source is pinned by Git blob in SOURCE_MAP.json and copied byte-exactly as PARENT_runner.py, fixture.py, audit.py and PARENT_schedule.json. build_successor.py changes only successor metadata plus the parent DISPLAY/XAUTHORITY scope/restore and asserts the exact successor runner SHA-256.

Live construction/formal remain forbidden until AUTHORIZATION.json is changed by an explicit fresh #60 grant.
