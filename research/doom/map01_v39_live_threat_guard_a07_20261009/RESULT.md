# A07 retained outcome

**Disposition: HOLD.** The run completed all 10 planner turns in 41.60 seconds of control time. It remained alive, with no deaths, zero kills, and no MAP01 exit. Typed observations ranged from health 100 to 82 and ammo 48 to 36.

The hard-health guard did not trigger, and the independent scorer recorded no useful kill/exit event during pending inference. The requested live threat-control gate therefore remains open.

The original raw auditor emitted `FAIL` because it required an `input_released` event for every matched cancellation. Additive audit v2 reconciles input admissions: all 10 cancellations matched and all 10 terminals had verified empty releases. Six covers admitted inputs; each had a matching `input_released` event and complete per-key release evidence. Four were cancelled before any input admission or per-key transition, so no input-release event was due. The release-safety portion is scoped PASS; the overall preregistered research outcome is HOLD. Both audit versions and raw data are retained without overwriting the original.

The complete raw output, freeze, request/response protocol, session traces, frames, score, both audits, result, and SHA-256 manifest are retained under the ignored local allocation directory `results-local/doom/map01-v39-live-threat-guard-a07-20261009/`. The PR carries the preregistration, reproducible audit correction, and this compact outcome; the raw files remain local because they include the full captured image/protocol set.
