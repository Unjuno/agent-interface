# Issue #4313 — retained result and integration handoff

## Chronology and ownership

The 42-session `resume_json_ingress_c7e4_v3` pilot was locally source/gate-frozen and completed in a preceding conversation. Its GitHub publication is retrospective. This continuation performs read-only reconstruction and evidence delivery only: fresh GUI runs, policy workers and formal reruns are all zero.

Intake main: `40493a9bb77eba00dd9d72207d683f2206ea45a5`. README, CURRENT_GOAL, ROADMAP, recent open/closed Issues, PRs, first 100 branch names, #4307 comments and exact/related ingress searches were checked. Coverage is bounded; unpublished work is unknown. The active v2 engineering publication and #4307 prospective nested-frame allocation are untouched.

Owned branch: `research/resume-json-ingress-retained-c7e4-20260924`. Only new files in `research/integration/resume_json_ingress_delivery_c7e4_v1/` are proposed. This is not a shared runtime patch.

## Retained measurements

| Endpoint | LEGACY_JSON | STRICT_AFTER_PARSE | STRICT_RAW |
|---|---:|---:|---:|
| Fresh original pilot sessions | 14 | 14 | 14 |
| Correct child completion | 14/14 | 14/14 | 14/14 |
| Stable root completion | 2/2 | 2/2 | 2/2 |
| Invalid root continuation on malformed receipts | 6/8 | 2/8 | 0/8 |
| Invalid root continuation on typed false-state receipts | 2/2 | 2/2 | 2/2 |
| Total invalid root continuations | 8 | 4 | 2 |
| Root refusals | 4 | 8 | 10 |

These are directed counts, not natural failure rates. A final root string `ab` is not task success after the task was canceled. No arm passes all-source truth/currentness safety. The original local characterization label is retained without changing it to a formal or production PASS.

Frozen raw-only audit: 5,580 checks, errors=[]; 15/15 effective evidence corruptions reject; frozen source 15/15 unchanged. Original 126 app/server/policy exits, 42 case launcher exits and seven batch launcher exits are all 0. There were 146 native taps, 292 app key events and 42/42 neutral terminal server states.

## H / T / D / C / U

**H:** last-member-wins JSON decoding can erase duplicate-member evidence before dictionary validation. Strict original-byte parsing should reject the malformed forms before fixture input while preserving stable continuation. Format validation alone cannot establish actual task liveness.

**T:** seven scenarios (STABLE, CANCELED_NATIVE, CANCELED_TEXT, UNKNOWN_LABEL, DUP_TRUE, DUP_FALSE, TYPED_LIE), three policies, two repetitions: 42 sessions in seven immutable six-case batches. Two-level private Tk interruption, actual XTEST prefix/suffix, separate policy worker and app-owned event/effect journals. One first execution per batch; no rerun, replacement, exclusion or postfreeze tuning. Publicly preregistered formal allocations: zero.

**D:** the original local gate required all 42 records/exits, the exact expected contrasts, raw audit errors=[] and all 15 effective corruption controls rejecting. These passed. The declared typed-false control remains unsafe in all arms, so the gate is boundary characterization, not a universal safety gate. This continuation requires exact original bytes and byte-identical audit/control reproduction before evidence delivery is qualified.

**C:** a strict upstream parser can make a dictionary-only API appropriate. A different trusted source contract can rule out malformed inputs. The weak arm is intentionally authored and is not an allegation about deployed runtime behavior. A type-correct lie and a truthful receipt have the same representation; schema validation cannot supply missing source truth.

**U:** no source authentication, real-world currentness guarantee, generation ownership, replay protection, ancestor-cancellation completeness, atomic check/use, arbitrary GUI/platform transfer, model utility, token/latency gain, natural incidence or product claim. Same-author separate implementations are not independent human review.

## Environment and measurement boundary

Original supplied Linux x86_64 execution container, CPython 3.13.5, Tk 8.6.16, Python-Xlib 0.15; per-case authenticated TCP-disabled Xvfb, 640x480x24. No Docker/OrbStack image-attestation claim. CPU/frequency/load were not pinned. No provider/model, user desktop/data, package installation or experiment network. Key neutrality is X-server logical state, not physical HID telemetry. No latency benchmark or calibrated combined timing uncertainty is claimed.

All counts are dimensionless. Diagnostic monotonic timestamps retain their native nanosecond unit; no clock conversion is used to infer task success. The proof and symbol/domain/unit table are preserved in `retained/PROOF.md`.

## Continuation verification and preservation

All 558 original v3 files were restored unchanged. The 557 original manifest entries and 15-file freeze match. `verify_readonly.py` returned exit0 and reproduced the old audit and all controls byte-for-byte. Eight new packaging refusal checks also passed. No scientific case was restarted. The original construction failures, rejected prefreeze and then-true write-unavailable statements remain byte-identical; this later publication does not rewrite their chronology.

## Integration decision and bounded roadmap

A receipt interface must specify whether original JSON representation is validated before lossy normalization, and separately how source truth and current task state are established before consequential continuation. Parser success, authority, release and task completion remain distinct.

Completed locally: immutable restore -> source/manifest check -> unchanged raw-only audit/controls -> bounded capsule/unpacker -> packaging rejection checks. Remaining remote gates are exact object readback, evidence PR, applicable exact-head CI/review, qualified main readback and dependency-safe owned-branch cleanup. Current Issue/PR comments record actual progress; this report does not pre-assert a merge.

This result informs #2789 recovery but does not close #4307, #57 or the global ROADMAP. No automatic new experiment is needed to make this favorable; the retained source-truth limitation remains binding.

Primary API background: Python 3.13 JSON documentation, repeated names and object_pairs_hook, https://docs.python.org/3.13/library/json.html. API documentation explains parsing behavior; all GUI counts come solely from the retained pilot raw evidence.
