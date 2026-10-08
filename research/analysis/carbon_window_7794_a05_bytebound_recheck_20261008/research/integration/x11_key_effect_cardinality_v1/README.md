# Live key-state and text-effect cardinality — Issue #4032

**First formal result: PASS_KEY_STATE_EFFECT_CARDINALITY_BOUNDARY_SCOPED.**

Date: 2026-09-22 JST (raw UTC records are 2026-09-21). Successor to closed #1001; related #651, #5, #57 and #2789. This is live Xvfb/Tk evidence about distinct measurement quantities, not a new operating-system theorem, production InputOwner test or model-quality result.

## Result

One source-frozen allocation `key-cardinality-4032-01` completed two fixed batches and all twenty fresh ordinary Tk Entry processes. No formal retry, replacement, source change or threshold tuning occurred. Both runner exits, both outer supervisor exits, twenty receiver exits and both Xvfb exits were observed as zero; private display sockets were removed. Every measured terminal and cleanup keymap/button state was neutral.

Each table value is **per case**, not a pooled sum. E is only the sampled logical X-server UP-to-DOWN transition count around explicit commands. It is not hardware telemetry or continuous state history.

| Schedule | Repeat mode | Cases | D: explicit down calls | E: sampled down transitions | P: native KeyPress | V: inserted characters |
|---|---|---:|---:|---:|---:|---:|
| No input | Both | 4 | 0 | 0 | 0 | 0 |
| Single tap | Both | 4 | 1 | 1 | 1 | 1 |
| Duplicate down, no intervening up | Both | 4 | 2 | 1 | 1 | 1 |
| Two distinct taps | Both | 4 | 2 | 2 | 2 | 2 |
| Long hold | OFF | 2 | 1 | 1 | 1 | 1 |
| Long hold | ON | 2 | 1 | 1 | 10 | 10 |

The frozen long-hold ON gate was **more than one** inserted character, not exactly ten. Construction produced nine and remains excluded. The nominal hold was 650 ms; observed down-sync-end to up-call-start intervals were 650.695321–683.380377 ms across the four long holds. These are scheduling-dependent intervals, not performance claims. Requested/read-back repeat delay and interval were 250/50 ms in both batches.

Native and Tk **press** time/state/order and ordinary Entry value progression agreed in all twenty cases. Native release streams included additional leading releases not exposed by Tk callbacks: twenty additional native releases in total. All native/Tk events are retained. The cause was not established; none is reclassified as a hardware edge or character effect.

## Decision and integration handoff

A completed down request is neither proof of a fresh logical down transition nor proof of exactly one application effect. Preserve separate request, logical-state and application-effect fields. For example, using two admitted down requests as a two-character postcondition would mis-score the duplicate-down cases, while treating one held down as one character would mis-score repeat-enabled long holds.

This supports the completion-level separation discussed by #5 and the evidence/acceptance separation in #57/#2789. It does not mandate changing the InputOwner ABI: surrounding trusted context or a task-specific independent postcondition may supply the missing information. Do not infer production impact from the isolated native primitive.

## Evidence and verification

The readable source/gates were committed **before formal** at `f3c2c0a042db53394cd9d529c0c199ba235f60f3`. Intake main was `1f798cbb60b929e738c6bf8a5912470b38b45ff4`. All eight published source/plan/environment/freeze Git objects matched local bytes. `FREEZE.json` is an immutable preformal snapshot: `formal_started:false` describes that snapshot, not the later execution status.

The unchanged raw-only auditor completed **1,872 checks**, twenty rows, zero integrity errors and zero scientific-gate failures, exit zero. It does not import Xlib, Tk, the controller or receiver. This is a separately structured implementation/process by the same author, **not independent human review**.

All **twelve semantic corruption controls** were rejected: altered command, keymap, actor, final/native evidence, button state, exit status, clock, barrier, effect, focus and repeat configuration. Mutations update duplicated stdout as well, so rejection is not only a redundant-copy mismatch. Four unit-test methods also pass against ten retained construction positives and malformed/extra-command cases.

After formal, all ten recorded executable/module/library SHA-256 values were recomputed and matched `ENVIRONMENT.json`. Source files also remained unchanged. Hash equality demonstrates byte identity, not external trust or universal reproducibility.

- `AUDIT.json` SHA-256: `2c76b12f4ff8338282ab077c4a0465f264bd58b781ef5e4a0866aa185936ac9a`.
- `CORRUPTION.json` SHA-256: `dfe03348ecb47277f26ca3c5646ad0c43627dadafdcc0722c967bbd206ce4425`.
- `FREEZE.json` SHA-256: `61d5986444beb4f61cb66dac1bf6560188f98dd8f7c6de64b7cff3ce8be1dd72`.

`evidence.tar.xz` is a lossless archive of the original source versions, construction failures, formal raw rows, per-process exits, stdout/stderr, frozen plan, audit output, corruption tests, descriptive intervals and CSV. `ARTIFACTS.json` records its length/hash. The archive contains a member-by-member SHA-256 manifest. No credentials, cookies, screenshots, user documents or host display inputs are included. The authentication *pathnames* in raw command receipts are retained, but the temporary cookie bytes are not.

## Read-only reproduction

Inspect the readable source before running it. The archived auditor needs only the Python standard library. These commands replay evidence; they do not launch X11 or rerun the experiment:

```sh
mkdir replay-4032
python - <<'PY'
import hashlib, json, pathlib, tarfile
archive = pathlib.Path('evidence.tar.xz')
expected = json.loads(pathlib.Path('ARTIFACTS.json').read_text())['archive_sha256']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
with tarfile.open(archive, 'r:xz') as tf:
    tf.extractall('replay-4032', filter='data')
PY
(cd replay-4032 && sha256sum -c MANIFEST.sha256)
python -B replay-4032/audit.py replay-4032 > replay-audit.json
(cd replay-4032 && python -B -m unittest -v test_audit)
python -B replay-4032/test_audit.py --formal replay-4032/formal/batch-0/case-01/row.json
```

Do **not** run `study.py` or `supervise.py` against the consumed allocation. A future live replication needs a separately recorded allocation, reviewed environment and prospective bounds; it must not replace these rows.

## Retained failures and limitations

`construction-01` stopped before any XTEST input on a Tk/native focus mismatch; actual receiver cleanup exit was -15, server exit zero. `construction-02` used the explicitly focused Entry and completed ten c-letter cases. The first construction auditor then failed eight input-bearing rows because it imposed an extra native/Tk release-equality rule. Before formal, that rule was changed to exact press equality and ordered inclusion of Tk releases in the retained native stream, matching the original Issue's press/value question. Both auditor versions and the first failed test output remain available; no live rerun was used to repair the audit. See `CONSTRUCTION.md` and the public preformal Issue comments.

Preformal code review also hardened receiver and supervisor timeout termination. Normal completion was exercised by formal; these timeout fault paths were not separately fault-injected. No timeout/release watchdog robustness claim follows.

The study used the provided Linux x86_64 container, CPython 3.13.5, Tk 8.6.16, private authenticated TCP-disabled Xvfb and one ASCII letter. Docker/Podman were absent locally; no Docker/OrbStack image or fleet-wide absence is asserted. Native XTEST emission resembles the reviewed ordinary-down primitive, but the complete InputOwner, runtime, public CLI, planner and task-level authority path were **not** executed. No IME, alternate layout, general application/game behavior, physical device edge, model benefit, token saving, latency superiority, reliability estimate or product promotion is established. Neutral input does not undo inserted text.

The scoped scientific allocation and audit are complete. Publication/merge status is tracked in the associated PR/Issue rather than inferred from this report. The overall ROADMAP, #57 and #2789 remain open; no broad acceptance gate is closed by this component result.
