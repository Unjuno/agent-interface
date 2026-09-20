# Issue #2918 live MANIPULATE_TO certificate transfer — allocation 01

## H/T/D/C/U

**H — hypothesis**  
The exact #1904 minimum-certificate compiler can derive a decision certificate
from facts extracted from a fresh public X11 observation, and that certificate
can safely suppress forwarding when only facts outside its mask change, while
masked-fact changes and uncertain/stale/unbound observations fail open.

**T — single bounded allocation**  
Use a disposable X11 fixture with visible color-coded `T,D,E,S` fact cells.
Facts are read only from pixels in the returned image of the public
`runtime.cli_v1.observe` API; the candidate must not read the fixture state
file or oracle. The frozen #1904 `model.py` supplies branch semantics, minimum
certificate selection and `PHASE_SUPPORT`. A separate independent auditor
re-derives truth and certificates from a sealed table implementation and the
post-run fixture oracle.

Fixed case order, with no replacements:

1. `complete_initial`: `EFFECT_PENDING`, `(T,D,E,S)=(1,1,1,0)`, derive `ES`,
   initial disposition `FORWARD`.
2. `complete_unmasked_change`: `(0,0,1,0)`, same binding/intent, `E,S`
   unchanged; candidate should `SUPPRESS` a downstream forward. Phase-union
   and global-support controls should `FORWARD` on changed dependencies.
3. `complete_masked_change`: `(0,0,0,0)`, `E` changed; candidate should
   `FORWARD` and the independent terminal decision should change.
4. `abort_initial`: `PREPARE`, `(1,0,0,1)`, derive `S`, initial
   `FORWARD` under a new intent.
5. `abort_unmasked_change`: `(0,1,1,1)`, same binding/intent, `S` unchanged;
   candidate should `SUPPRESS`; phase-union/global controls should `FORWARD`.
6. `missing_fact`: one fact cell has an unknown color; `YIELD`.
7. `partial_observation`: requested region excludes a required cell; `YIELD`.
8. `contradictory_fact`: duplicated visible `D` cells disagree; `YIELD`.
9. `stale_observation`: one real capture is held beyond the frozen 250 ms
   freshness bound before decision; `YIELD`.
10. `target_replacement`: the original X11 window is replaced and its binding
    changes; old certificate cannot be reused; `YIELD`.
11. `ambiguous_target`: two windows match the frozen target role; `YIELD`
    before observation/certificate use.
12. `intent_epoch_mismatch`: a complete observation is paired with a different
    intent epoch; `YIELD`.

Each observation is a single read-only public API call. There are no input
actions or authority grants. The fixture records a separate oracle log that is
unavailable to the candidate and is read only after the one-shot allocation.
The fixed source/image/runtime, target resolver, pixel coordinates and RGB
palette are frozen before construction testing. Construction tests are
excluded from the formal allocation. After construction passes, run exactly
one formal container invocation, then one independent read-only audit
container. Never rerun or tune after the formal start.

**D — decision**  
`PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED` requires all 12 cases retained;
exact source/image/input hashes and API receipt lineage; the two preregistered
unmasked transitions safely suppressed while phase/global controls would
forward; the masked transition forwarded; every stale, missing, partial,
contradictory, replaced, ambiguous and epoch-mismatched case fail-open; zero
unsafe suppressions; independent terminal-decision reconstruction; and clean
fixture/X-server cleanup. `FAIL_UNSAFE_SUPPRESSION` if any uncertain or changed
required fact suppresses; `HOLD_CERTIFICATE_PROVENANCE_UNAVAILABLE` if the
public observation cannot bind facts to the current intent/target/epoch;
`STOP_SETUP` if no valid observation row is produced; `HOLD_NO_LIVE_NARROWING_GAIN`
if safe but neither unmasked case narrows the live support decision.

**C — constraints**  
OrbStack Docker 29.4.0, Linux/arm64, pinned local X11 route-test image by
immutable image ID, `--network none`, read-only root/source, isolated `/tmp`
and separate writable output. Only a private Xvfb fixture and the public
read-only observation API are used. No model/provider, external network, GUI
input, task mutation, or production/default-runtime claim. The independent
oracle never feeds candidate extraction or certificate generation. #1904 and
all predecessor outcomes remain byte-for-byte unchanged.

**U — unknown**  
Whether live public-API image bytes and target/epoch receipts can establish
the exact small set of current dependencies needed for safe state-conditioned
suppression, and whether the resulting reduction remains safe under partial,
contradictory, stale, replaced and ambiguous evidence. This fixture does not
measure real observation cost savings because each case is still captured for
independent audit.

## Frozen inputs and output boundary

The exact #1904 compiler source SHA-256 is
`a6247953fa3a25051866c97d37d6eb053dd63f76b5573e05e494cab03c065eb2`.
Base main is `e6f74d3b9fef0467327823ab97cb15f0dbe59ac4`. The full source/image
manifest and one-shot invocation are committed before any formal fixture
observation. Formal raw data, screenshots, independent audit, failures and
container cleanup receipts are retained only under this new allocation path.

The immutable container is local image
`sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`
(`linux/arm64`). The source and exact commands are listed in `SOURCE_FREEZE.json`.
Construction-only evidence consists of compile/import/certificate checks and a
synthetic PNG pixel/reuse/staleness check; neither started Xvfb nor called the
public API. The formal allocation is one container invocation of
`run_live_allocation.py` on a private Xvfb server, followed by one independent
read-only auditor container. Do not use `xvfb-run`; its construction smoke
startup hung before Python launched. The explicit Xvfb startup path is frozen.
