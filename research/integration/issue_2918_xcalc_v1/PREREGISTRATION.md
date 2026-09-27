# Issue #2918 XCalc second-surface transfer — formal-01

Status before execution: preregistered, not run. The experiment tests the
posted #2918 hypothesis on a second application surface; it is not a rerun of
allocation 05 and does not alter any predecessor.

## H / T / D / C / U

**H — Hypothesis.** The unchanged #1904 minimum state-conditioned certificate
compiler can consume four Boolean facts derived from the visible decimal
display of a real XCalc window through the public `runtime.cli_v1.observe`
boundary and preserve its bounded FORWARD/SUPPRESS behavior. Complete fresh
observations with unchanged terminal semantics may suppress only when the
previous certificate's mask permits it. Partial/missing/unrecognized/stale
pixels, contradictory XID, ambiguous targets, a changed X11 client/window
identity (including XID reuse), or a changed intent epoch must YIELD before
certificate reuse.

**T — Frozen target.** Run one 13-row XCalc allocation in private Xvfb with the
pin-stated XCalc/X server image. Primary rows are:

1. `EFFECT_PENDING`, 14 → 10: only D changes; prior minimum mask ES; expected
   SUPPRESS and unchanged independent outcome COMPLETE.
2. `EFFECT_PENDING`, 10 → 12: D and E change; prior ES; expected FORWARD and
   independent outcome changes COMPLETE → CONTINUE.
3. `PREPARE`, 12 → 14: only E changes; prior minimum mask DST; expected
   SUPPRESS and unchanged independent outcome READY.

The other two admitted rows establish each phase's initial certificate.
Eight fail-open controls cover clipped/partial image, missing display ROI,
unrecognized 99 display, stale capture (>250 ms), contradictory candidate XID,
replaced client/window, two same-role XCalc windows (zero observe calls), and
intent-epoch mismatch. The replacement case is specifically gated on XRes
proving the same XID/resource base is owned by a different XCalc PID and a new
caller window generation.

**D — Decision and oracle.** The candidate receives only the public observe
reply, frozen pixel-template table, caller binding/intent, and prior
certificate. The certificate compiler is unchanged `model.py` from #1904.
An independent read-only auditor verifies API receipt and PNG hashes, derives
the visible integer from a separately implemented pixel hash table, maps it
to T/D/E/S, recomputes minimum certificates by exhaustive enumeration, checks
the terminal semantic truth table, binding and epoch lineage, all fail-open
rows, and phase-support/global-support controls. The expected primary outcome
is two safe candidate suppressions, one incremental suppression over
phase-support (two over global support), zero unsafe suppressions; the
PREPARE E-change is already suppressible by phase support. Acquisition and
capture-to-certificate time are reported separately from semantic disposition.
Three frozen corruption controls must reject a wrong candidate disposition,
missing row, and mutated PNG without modifying raw evidence.

PASS only if all 13 rows, 12 public API calls, independent audit, and all three
corruption controls satisfy the above. One runner invocation and one normal
auditor invocation; do not rerun or tune after formal outcome. If infrastructure
prevents execution, preserve STOP with diagnostics. If raw/audit integrity is
incomplete, HOLD. Any unsafe suppression or semantic mismatch is FAIL.

**C — Constraints.** OrbStack Docker 29.4.0; exact image digest is recorded in
`SOURCE_FREEZE.json`; linux/arm64; network disabled; read-only root and source;
bounded CPU, memory, PID count, and writable `/tmp`; dedicated output mount.
XTEST key/click injection is only deterministic fixture stimulus inside
private Xvfb. The public observer must report `input_dispatched=false` and
`side_effect_authority=false` for every observation. No model/provider call,
real host desktop, autonomous task action, user data, or production authority.
No masks, thresholds, cases, or image templates may be changed after formal
execution. Prior STOP/HOLD artifacts remain untouched.

**U — Update question.** Does the live observation-boundary transfer work on
an actual second X11 application surface when visible state extraction,
independent terminal scoring, and native-client identity (including XID reuse)
are included? This allocation does not answer held-out-app generalization,
post-effect correctness, model usefulness, end-to-end benefit, or release
readiness.

## Provenance model

- Observation epoch: the public observe `observation_id`.
- Intent epoch: fixed per primary sequence and changed in the dedicated
  mismatch control.
- Native binding: display, XID, XRes client resource base and local PID, plus a
  monotonically assigned caller window generation and role.
- Fact provenance: public artifact SHA-256 plus pixel SHA-256 for the frozen
  XCalc display ROI `[198,5,37,27]`; four Boolean facts are the binary digits of
  the independently visible decimal integer.
- Certificate lineage: phase, state, minimum mask, prior mask, changed facts,
  binding/intent/observation epochs, capture end and certificate-generation
  monotonic timestamps.
- Independent outcome: #1904 phase truth table evaluated on the state parsed
  from the retained public PNG. No GUI action is authorized, so no application
  post-effect or task-completion claim is made.

## Construction context (not formal evidence)

The exact 16 display templates were collected before formal registration and
recovered 16/16 with zero construction misclassifications. A separate XCalc
replay of value 8 produced an identical full PNG SHA-256. Exploratory pilot 03
showed XID reuse could alias a replacement window; its candidate output,
unaudited state, and audit-harness failure are preserved under
`construction/pilot_03_xid_reuse_hold/`. The XRes PID/generation binding was
added before this preregistration. Full construction STOP/HOLD history and the
audited rehearsal are under `construction/`; none is pooled into formal-01.
