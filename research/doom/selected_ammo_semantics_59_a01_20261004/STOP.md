# A01 STOP record

The frozen container command was issued once. It stopped at game initialization because the image did not contain the configured `doom2.wad`; no game state was created. WSLc also reported unavailable swap-limit/cgroup support. The container log preserves the initialization traceback. The host command runner returned a nonzero status, but its attempted exit-code sidecar was misdirected by PowerShell argument binding and was not retained; do not treat that missing sidecar as evidence.

The freeze's `created_utc` was manually entered as 2026-10-04 12:30 UTC, later than the retained container log timestamp 12:27:49 UTC. This chronology defect means A01 must not be considered a valid preregistration or scientific result. Its STOP is preserved as setup evidence only; A02 is separately labeled and uses explicit `freedoom2.wad`.
