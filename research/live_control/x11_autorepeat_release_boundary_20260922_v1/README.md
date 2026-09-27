# Retained X11 release-event boundary — Issue #4041

Research-only retrospective publication of the completed allocation
`autorepeat-release-c7e4-20260922-01`. No new GUI, XTEST, model or formal allocation
was executed in this delivery continuation. The source/plan freeze was local on
2026-09-21 at 21:17:43.239208 UTC, before the three original batches. Issue #4041
was created afterward; it is not public preregistration.

The original 309 files, all original paths and every byte are preserved in the
lossless capsule. `RETAINED_REPORT.md`, `FREEZE.json`, and `SUMMARY.json` are exact
copies. Their old `STOP_GITHUB_WRITE_ACTION_UNAVAILABLE` and `main_integration=false`
statements describe the preceding session and are intentionally unchanged.
This README records subsequent publication; current PR/CI/main state must be
read from GitHub, not inferred from the historical summary.

## Executed result and scope

**PASS_X11_REPEAT_RELEASE_BOUNDARY_SCOPED**. Five conditions, three fresh Tk Entry
sessions each, with two simultaneous native observers on the same private target:
legacy delivery and explicitly negotiated per-client detectable autorepeat.

| Condition (three sessions) | Authored down/up pairs | Legacy releases / query still DOWN | Detectable releases / query still DOWN | Entry characters |
|---|---:|---:|---:|---:|
| No input | 0 | 0 / 0 | 0 / 0 | 0 |
| Short 20 ms hold | 3 | 6 / 3 | 3 / 0 | 3 |
| Long 320 ms hold, repeat enabled | 3 | 36 / 33 | 3 / 0 | 33 |
| Long 320 ms hold, repeat disabled | 3 | 6 / 3 | 3 / 0 | 3 |
| Two short taps | 6 | 12 / 6 | 6 / 0 | 6 |
| Total | 15 | 60 / 45 | 15 / 0 | 45 |

DOWN means the server logical keymap at the bracketed query, not hardware state,
continuous observation, or reconstruction of event-time state. Of 45 legacy
release/DOWN witnesses, 30 are later same-hold repeat pairs and 15 are
onset-compatible pairs, including disabled-repeat controls. The onset cause
was not isolated. Detectable negotiation changes the observing connection's
representation; it does not suppress the application's repeated text effect.
X.Org documents the mechanism; this is not a new OS-defect claim.

## H / T / D / C / U

H: client release events, sampled server neutrality and application effects are
separate claims. T: one private authenticated TCP-disabled Xvfb/Tk/XTEST fixture;
15 sessions / 30 observer views in three fixed batches; repeat delay 80 ms and
interval 25 ms read back. D: all case/source/effect/release/exit gates reconcile,
no detectable release sampled DOWN, final and cleanup inputs neutral; all 66
recorded actor/configuration/runner/server exits zero and later PID absence.
C: supplied Linux x86_64 / CPython 3.13.5 execution container; no Docker/OrbStack
image identity, host desktop, user data, model/provider or experiment network.
U: other applications, hardware/backends, grabs/focus/reconnect, production
integration, model utility, tokens, latency and human-tempo benefit remain open.
There is no calibrated timing uncertainty, natural failure-rate or speedup claim.
Full preformal plan, definitions/unit table and gates are in restored `PLAN.md`.

## Preserved auditor failure, not a hidden rerun

The frozen original auditor passed at the original path but rejected intact
relocation because of an absolute-path assumption. That also confounded its
initial mutation checks. All original passing/failing audits and source remain.
The separately versioned postformal `audit_v2.py` repairs command-path provenance,
not scientific gates: 3,773 checks pass; 13 corrupted copies reject only after
each intact relocated copy first passes. No formal case/source was changed or
rerun. Independent implementation/process here means the same author, not an
external human reviewer.

## Inspect and reproduce without input

The 11 binary parts concatenate to 63,900 bytes (XZ JSON file map), binding all
309 source/raw/construction/metadata files and 648,410 expanded member bytes.
`CAPSULE.json` records every part SHA-256, expected Git blob, decoded hash and
original supplied ZIP hash. Checksums bind bytes; they are not authentication.

From this directory, with a new destination:

```sh
python -B unpack.py /tmp/autorepeat4041-review
cd /tmp/autorepeat4041-review
python -B verify.py
```

The unpacker validates bounds, hashes, paths, uniqueness and all decoded bytes
before writing. It never executes a binary or experiment. The verifier checks
308 manifest entries and 201 formal raw-file identities,
reproduces the exact audit and checks 13 corruptions. Do not run the consumed
`run.py` or `execute.py` formal commands. The directly readable `observer.c` is
the exact original private-window-only observer, not a production collector.

Fresh capsule restoration matched all 309 original files and reproduced the
same read-only verifier result. Seven packaging negative controls also refused;
see `PUBLICATION_CHECK.json`. Repository CI/review is a separate gate.

## Integration decision and parallel ownership

`CURRENT_PATH_REVIEW.md` records the current backend inspection: `release_all`
already queries server key/button state, rather than counting received releases.
This evidence therefore supports preserving that distinction, not a production
bug allegation, a reason to replace the collector, or a validated runtime patch.
Application effect must still be scored separately.

Closed #1001/#651 are preserved. Parallel #4032 owns its own command/state/text
cardinality experiment; no cases are pooled or repeated, no branch or gate is
changed. Only this additive namespace is published. #57/#2789 and the global
ROADMAP remain open. Bounded delivery: original-byte re-audit -> complete capsule
and readable source/report -> remote identity check -> PR/checks/review -> main
readback if qualified -> only owned dependency-safe supported branch cleanup.
