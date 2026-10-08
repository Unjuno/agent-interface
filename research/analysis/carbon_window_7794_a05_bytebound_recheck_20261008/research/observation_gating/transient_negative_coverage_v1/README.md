# Transient negative evidence requires measured coverage

Issue **#3948**, a narrow successor to **#2131** (`STALE_OR_MISSED`) and retained #455 / PR #479. Allocation: `transient-negative-coverage-20260922-01`.

**Result: PASS_TRANSIENT_NEGATIVE_COVERAGE_SCOPED.** One frozen local run completed 24/24 cases. A separate frozen raw-only audit returned zero errors and rejected 12/12 corruption controls. This is an observation-contract result, not GIL improvement, model utility, task success, or runtime promotion.

## Finding

A current clear frame does not prove that no transient cue occurred earlier. A nominal polling interval does not prove that the sampler actually covered the interval. Preserve `UNKNOWN` when coverage or a genuine duration bound is missing. Conversely, a retained positive sample reports historical `SEEN`, not current presence or input authority.

The question scored here is **whether a cue occurred during the measured interval**, not whether it is present in the final frame.

| Live scenario | Cases | Any-hit-or-absent baseline | Measured-coverage policy |
| --- | ---: | --- | --- |
| Clear, continuously sampled | 6 | ABSENT | 6 ABSENT_MIN_DURATION |
| Clear, intentional sampling gap | 6 | ABSENT | 6 UNKNOWN_COVERAGE |
| Cue entirely inside sampling gap | 6 | **6 false historical absences** | 6 UNKNOWN_COVERAGE |
| Sampled cue, then clear final frame | 6 | SEEN | 6 SEEN |

The latest-frame-only baseline reports historical ABSENT for all 12 actual pulse cases, although its final-frame *current-state* description is correct. Candidate false historical absences: **0**. All 24 outputs are non-authoritative.

## H — sufficient coverage bound

Let each capture sample the declared tile at an instant `s_i` within its measured bracket `[a_i,b_i]`. For a trace spanning `[T0,T1]`, define

```text
G = max(b_1 - T0, max_i(b_(i+1) - a_i), T1 - a_n).
```

For a known minimum continuous cue duration `w`, a no-hit trace can certify **no such cue wholly contained in the interval** only under the declared identity/predicate/clock assumptions and the strict sufficient condition `G < w`. Otherwise return UNKNOWN; unknown or malformed `w` never certifies absence.

Proof: consecutive actual capture instants are separated by at most `b_(i+1)-a_i`; leading and trailing gaps are bounded by the other two terms. A continuous cue avoiding every capture must fit within one of these gaps. None can contain a cue of duration at least `w` when `G<w`. This is a sufficient, possibly conservative condition, not an optimality claim. Strict inequality avoids endpoint ambiguity.

The proof does **not** exclude shorter cues or cues straddling the interval boundary. It assumes a coherent exact-predicate snapshot at some instant within each bracket. A timestamp field or surface string alone is not proof of clock identity or trustworthy transport.

## T — frozen experiment

The public preformal freeze is in Issue #3948, comment `5766208713`. Intake and preformal main: `b2457b746a6df06f6536585dfe2ab937aff639f4`. All new repository files are confined to this directory; historical results, runtime, README and global ROADMAP are unchanged.

A native C/Xlib subprocess creates a fresh 32x32 window for each case and draws an exact green cue or a clear control. The Python sampler captures full tile bytes; a separate X11 connection witnesses the pulse. The candidate receives only its own trace, never the fixture scenario, native draw events or witness pixels. Two losslessly deduplicated byte arrays retain every distinct complete pixel buffer; 270 sampler captures and 18 witness captures reference those hashes.

Fixed schedule: `[clear_covered, clear_gap, pulse_gap, pulse_observed]` repeated six times. Requested sampling sleep: 2 ms. Explicit fixture minimum duration: 6 ms. Gap cases deliberately stop sampler acquisitions through the native pulse/control interval. This is a directed counterexample/contract test, **not a random miss-probability or scheduler comparison**.

Formal command, invoked exactly once:

```sh
python run.py --mode formal --freeze FREEZE.json --out formal-01
```

Environment: provided Linux x86_64 execution container, CPython 3.13.5, imported Xlib `(0,15)`, gcc 14.2.0, private Xvfb with TCP disabled. Docker CLI/OrbStack and container image identity were not available. No Docker-engine/image equivalence is claimed. Exact experiment source, fixture executable, Xvfb executable and imported Xlib source-tree hashes are retained. Native dependency paths are recorded, but a fully portable dependency-image closure is not established.

No model/provider, game, XTEST, keyboard/mouse injection or user desktop. All 24 native children exited 0; server termination/cleanup and neutral keyboard/buttons were verified. Formal and independent-audit process exits are both 0. Expected empty-Xauthority warnings are retained verbatim in stdout, not removed.

## D — decision and independent checks

Every predeclared formal gate passed: 24 ordered cases; six missed but independently witnessed gap pulses; six deliberately exposed pulses; UNKNOWN for both gap scenarios; at least one certifiable continuous clear case (observed 6/6); no candidate false absence; source/pixel/clock/surface/cleanup agreement. The auditor imports neither runner nor candidate, reconstructs pixel counts from full raw bytes, checks native/capture time ordering and surface identity, and independently recomputes decisions.

Twelve corruption controls reject missing/duplicate rows, altered counts, Boolean timestamps, wrong surfaces, missing child exits, authority promotion, integer-as-Boolean authority, Boolean-as-integer server exit, false witness counts, bad pixel bytes and a wrong freeze identity. Ten policy test methods cover strict equality, bracket uncertainty, missing duration, invalid types, missing data/bindings, and non-authority. A finite control set is not a proof of arbitrary auditor soundness.

Raw SHA-256: `fc7a15404728cf501e3a91e60a13ed123737bf71d5b16c7bb60489a7d8858c8c` (86,531 bytes).

Freeze SHA-256: `65a33351f5d1e8588cc3e5912e7e334341762ed50fd9d91ab7fe98693dd20454`.

Descriptive only: continuous-clear worst bracket gaps were 2.453–2.795 ms; pulse-gap gaps were 8.705–8.964 ms. Actual native pulse exposure was 6.083–6.125 ms. These observations are not latency-benefit or hard-real-time claims.

## C — retained construction failures and old evidence

`CONSTRUCTION.md` in the source bundle retains three preformal failures: missing Python distribution metadata; unavailable inherited Xauthority; and a latin-1-string pixel reply that required lossless conversion. Their source snapshots/STOPs remain separate. Construction-04's four live cases are excluded from formal counts. Final typed-auditor controls used only an explicitly re-bound in-memory *copy* of that construction input; original bytes are unchanged.

#493's latest coordination record identified its proposed ten-pair GIL run as already performed in #455 / PR #479; this study did not repeat it. #462's distinct source-first freeze was inspected, but `run.py` was not retrievable at the cited commit. That is an intake retrieval limitation, not proof the source never existed. No old allocation was consumed, overwritten, repaired in place or retrospectively relabelled.

## U — integration limits and handoff

Natural GUI events do not acquire a valid minimum duration merely because a caller supplies a number. Without an independently justified duration contract, the safe result remains UNKNOWN. The helper also trusts its input capture counts/identity; the independent audit establishes those bindings only for this frozen fixture. Do not turn this research function into production authority without a trusted live transport and source-specific contract.

This result addresses the negative-observation interpretation boundary in ROADMAP O3/O4 and #2789. It does not exercise the integrated six-task desktop entry path. #2131's model-facing comparison, #2789's integrated acceptance and the global ROADMAP remain open. No default GIL, shared runtime or broad product claim changes.

Bounded roadmap completed: predecessor/collision inspection -> H/T/D/C/U -> excluded construction -> public hash freeze -> one live experiment -> independent audit/corruption controls -> additive evidence publication. Integration and broader research are not marked complete.

The next smallest question is whether a real application can supply a trustworthy minimum-duration/temporal-completeness contract. An immutable event journal with explicit missed-event accounting is another possible source, but was not tested here. Do not assume a finite polling trace provides either guarantee.

## Verify without executing a live experiment

The complete source, fixture binary, freezes, construction history and formal raw/audit/logs are losslessly packaged for GitHub MCP text transport. `policy.py` is also exposed directly for review; unpacking verifies that it is byte-identical to the frozen source. No external font/model/credential is bundled.

Run from this directory, using a new destination:

```sh
python unpack.py /tmp/issue3948-review
cd /tmp/issue3948-review
python -m unittest -v test_policy
python audit.py formal-01/RAW.json --root . --out REVIEW_AUDIT.json
```

`unpack.py` checks compressed archive hashes, safe member paths, an expanded-size limit, every frozen source hash, the freeze hash and raw-result hash. It does not launch the fixture, Xvfb or a model, and does not grant executable permissions. The read-only audit needs only Python's standard library; live X11 packages are unnecessary for reviewing retained evidence.

**Do not rerun the consumed formal-01 allocation.** A future live study needs a distinct Issue/allocation/output, a freshly validated environment and a new preformal freeze. A newly compiled binary need not equal this preserved compiler output; changing its pin silently would invalidate this allocation.

Primary implementation references: Python `time` documentation (CLOCK_MONOTONIC / process-wide clock); X.Org XGetImage documentation (drawable rectangle capture). The sufficient bound and experimental conclusions above are derived and tested here, not borrowed performance claims.
