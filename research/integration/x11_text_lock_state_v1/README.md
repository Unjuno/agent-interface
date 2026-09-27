# X11 text: locked-state effect boundary (#4003)

**PASS_TEXT_LOCK_BOUNDARY_SCOPED**, one frozen 24-case allocation. This is a
backend-method / ordinary Tk Entry experiment, not production admission or a
new universally safe text implementation. Closed #3794 is preserved unchanged.
The specific #2789 integration blocker is mistyped text despite completed
backend execution and verified physical release.

## First-outcome observations

All four predeclared six-case batches ran once, with actual runner AND outer
supervisor exit0, no timeout, no retry/replacement/tuning. All24 fresh apps
exited0, all4 private Xvfb servers exited0 and removed their sockets. Native
XQueryKeymap/pointer queries found physical keys/buttons neutral after every
case; locked modifiers stayed at their configured dispatch state after release.

| Policy | Exact aB2 | Wrong Ab2 | Refused, empty Entry |
|---|---:|---:|---:|
| Exact original backend | 4 | 4 | 0 |
| Preflight-only LockMask guard | 2 | 2 | 4 |
| Dispatch-boundary LockMask guard | 4 | 0 | 4 |

Each cell below has two independent fresh app processes, but is a directed
repetition, not a sample of natural failure probability.

| Prepared -> dispatch lock | Exact backend | Preflight guard | Dispatch guard |
|---|---|---|---|
| OFF -> OFF | aB2 | aB2 | aB2 |
| ON -> ON | Ab2 | refusal | refusal |
| OFF -> ON | Ab2 | Ab2 | refusal |
| ON -> OFF | aB2 | refusal | aB2 |

Preflight-only caching therefore misses a newly locked state and also rejects
a currently unlocked state. Dispatch guards refused all4 current-locked cases
with zero backend emissions and zero app key events; unlocked cases produced
the exact requested text. All24 trailing-Euro preflight controls refused before
input. Each executed aB2 plan emitted8 paired key events; the ordinary Entry's
StringVar journal and its actual key-event character payload independently agree.

The exact backend and preflight-only controls separately remain
**FAIL_TEXT_EFFECT** for their wrong-case rows. A completed operation list and
verified release do not certify requested application text. The hypothesis PASS
is not a PASS for those unsafe controls, and refusal is not task completion.

## Evidence and independent reconstruction

Preregistered source commit: abb01bdfd9a5b47cec6a5cea50ea7eb78c42c7d8.
FREEZE.json SHA256: d07e3476c50c5763220b66208f8f302b88405b4039745715975dd1e000e20269.
All ten source/environment identities stayed unchanged through all batches.
The frozen raw-only audit exited0, errors empty,24/24 rows reconciled and10/10
copied-evidence mutations rejected. It checks raw/native/app wire binding, exact
case identities, program/event order, lock/focus/physical release and process
exits. It does not import the candidate runner or X11 backend.

Audit SHA256: 9695da7b25fa9bc9041a8b5d78ccb8fc8859fd925e94be4d799beb7afe86bc1a.
A fresh lossless restoration of all75 archived files and10 frozen sources was
checked; running only the retained auditor there reproduced byte-identical
stdout and observed exit0. No GUI or task was rerun. Separate implementation
and process is the audit boundary; no independent human/agent approval is claimed.

`EVIDENCE.json` binds five archive segments to one26,360-byte XZ archive,
SHA256 ffd49bd896b0168d60a1454119ba084fff234cdf057fd9d76fb42291db1f90a5.
It retains562,876 uncompressed file bytes: complete raw JSON/wires/key/value
journals, per-case copies, process receipts/stdout/stderr, native helper binary,
and both construction outcomes. Exact source is readable alongside this report.

## Preserved construction incident

construction-01 stopped before task input because parent Python-Xlib selected
an unrelated XAUTHORITY location, although the native helper and child app had
the private display credentials. Actual runner exit2, app terminated, own Xvfb
exit0/socket removed; its old run.py and partial raw are unchanged in the archive.
The parent auth mapping/restoration was corrected before formal freeze.
construction-02 used distinct payload cD3 and passed exact Entry effect, eight
events, neutral release and zero app/server exits. Both are excluded from the24
formal rows. Auditor typed schedule/clock checks and process-group timeout
cleanup were finalized before source freeze. No formal-source repair occurred.
This incident did not create a new administrative successor or fleet dependency.
Previous #3931/#3955 STOP/HOLD are neither rerun nor relabeled by these results.

## Read-only reproduction

From this directory, with Python3.13 (stdlib only for restoration/audit):

```sh
python -B restore.py --out /tmp/issue4003-readonly-fresh
cd /tmp/issue4003-readonly-fresh
python -B audit.py formal
```

Use a fresh output directory. The restore command verifies all archive segments,
archive/member bounds, regular safe paths, source freeze and critical raw/audit
hashes. It does not import/run GUI code or execute the native helper. The restored
consumed markers are intentional: do NOT rerun supervise.py or run.py against
this consumed allocation. A new experiment requires a new separately frozen
allocation and source/environment identities, not deletion of consumed markers.

Native helper source/build command and all measured environment identities are
in PLAN.md and ENVIRONMENT.json. The retained native binary is for byte-level
provenance, not an instruction to execute a downloaded binary on another host.

## Scope and integration decision

See PLAN.md for complete H/T/D/C/U, variable table, unit check and roadmap.
Environment: supplied Linux x86_64 execution container, CPython3.13.5, Tk8.6,
Python-Xlib0.15, private authenticated US Xvfb640x240x24. Docker/Podman and pinned
image identity unavailable; NOT Docker/OrbStack replication. No performance
benchmark is claimed; timestamps are same-domain diagnostic ns only.

The full upstream backend blob is exact9cae101a219348077668c8fc086acf8e13154afe.
The declared AST loader omits only the unused runtime.core_v1.contract import;
all executed classes/methods/constants are unchanged, no substitute helper is
provided. Public CLI/core admission, manifests and artifact methods are not
exercised. This limitation must follow any reuse of the result.

**Integration recommendation, not implementation:** require explicit handling
of locked keyboard state in text-route admission; never infer semantic text
correctness from physical neutrality, and do not silently toggle the user's
Caps Lock to repair a request. The research-only final check has a check/use gap:
no mutation occurs after it in this allocation, so concurrent changes during
focus/key emission, other modifiers/groups/IME and production correctness remain
unproven. A public-route test with controlled post-check mutation is the next
actual scientific boundary; this result alone does not justify deployment.

Related applications: input-method/HCI state awareness; concurrency freshness
of preconditions; software verification separating actuator receipts from
application postconditions. No model utility, token/latency gain, human-tempo,
German-layout replication or product qualification follows.

This bounded research is ready for evidence integration via PR. #2789 and the
repository ROADMAP remain open. Parallel reader/clipboard/semantic-abort sources,
old evidence and shared runtime remain untouched.
