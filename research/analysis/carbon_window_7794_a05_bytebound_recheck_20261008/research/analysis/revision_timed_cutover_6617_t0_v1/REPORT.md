# Issue #6617 T0 — revision-timed cutover finite event model

## Disposition

`PASS_METHOD_SCOPED`. The frozen WSLc candidate emitted 30 traces (10 scripted cases × 3 arms); a separate raw-only auditor exited 0, reported zero errors, and rejected all four preregistered corruption controls. Candidate/auditor/retry counts were 1/1/0. The result is limited to this deterministic logical-time model.

## H / T / D / C / U

- **H:** On the one frozen stable-turn schedule, version-bound read-only preparation will shorten logical time from committed final request to verified intended effect compared with final-only preparation, without allowing provisional/stale input in the safe arms.
- **T:** Final-only, deliberately unsafe naive-provisional, and exact-version-bound read-only arms across stable request, negation, recipient revision, quotation, speaker switch, post-revision stale completion, stop-before-input, unknown post-input effect, verified irreversible effect before stop, and urgent release during pending planner work.
- **D:** Passed the complete 30-row roster, scope/identity/authority input gates, stop/release distinctions, stable-case improvement, safe-arm zero-provisional-input condition, naive-comparator unsafe detection, and rejection of old-epoch, partial-as-final, speaker-merge, and cancel-as-undo corruptions.
- **C:** The result may depend on an easy stipulated schedule; final-only may be fast enough in real use; the safe arm discards changed candidates and has no benefit in those cases. The simulator and auditor share the same authored protocol assumptions.
- **U:** Scripted turns do not establish ASR quality, authenticated speaker identity, actual intent, human interruption behavior, GUI effects, real latency, safety, or product utility. Logical ticks are not time measurements.

## Result

For the stable scripted request, version-bound preparation reached the verified-effect marker 3 logical ticks after final commitment, versus 6 ticks for final-only preparation (3 stipulated ticks saved). The deliberately naive comparator emitted 9 provisional inputs; both safe arms emitted zero provisional, unauthenticated, or uncommitted inputs. The stop-after-accepted/unknown case did not allow retry or blind inverse. Stop-after-verified-effect was classified as already occurred and did not auto-undo. The independent urgent-release trace verified release before planner completion. All four corruptions were rejected.

## Formal execution and evidence

- Runtime: Microsoft WSL Containers (`wslc.exe`) 3.0.1.0, kernel 6.18.40.1-1; cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, Python 3.12.15, linux/amd64.
- Pull disabled, network disabled, source read-only, output on a separate writable mount. One CPU and 512 MiB were requested, but WSLc emitted the swap/cgroup unsupported warning; no resource-enforcement claim is made.
- No GPU was requested because the finite event simulation has no GPU-dependent computation. Docker and Podman were not used.
- Construction checks on CPython 3.11.9: 7/7 focused tests; bytecode compilation and `git diff --check` passed.
- Freeze, exact commands, runtime warning, counts, and hashes: [`formal_01_20261002/`](formal_01_20261002/). Raw SHA-256 `0edd1c334494d35b70e76ef54cb34afdbe08884c30bab4442a518151c9b044cd`; audit SHA-256 `206a6f82c5c2b5572bf5aa0a0d6374e8a8136b48e1d672222507046d0770698e`.

## Interpretation and next boundary

This closes only the synthetic T0 method gate. It does not establish that a voice-capable route exists or that provisional speech can safely authorize an effect. A prospective T1 would need its own allocation and explicit authority, isolated disposable voice/GUI fixture, independently established turn/effect truth, and real-time matched protocol. The existing Issue #6617 remains open for that unresolved empirical transfer question.
