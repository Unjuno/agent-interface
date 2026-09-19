# Text observation binding v1 — retained X11 result

**Result ID:** `text-observation-binding-v1-20260916-01`  
**Source/plan freeze:** `39d95351841307e5983b4d33e1f609f4ab0a0ed8`

## Disposition

**PASS_SCOPED_BOUND_PREFIX_RECOVERY / REJECT_CONTENT_ONLY_OBSERVATION_AUTHORITY / HOLD_PRODUCT_PROMOTION**.

One source-frozen private Xvfb/Openbox matrix executed exactly once against two real Tk entry targets. Intended text was `bookkeeperoffice`; stops were 3/5/8/12/15. Each stop ran six observation conditions under two policies, 60 trials total.

| policy | predeclared gates | exact target-A final text | refusals |
|---|---:|---:|---:|
| content-only prefix | 30/30 | 5/30 | 0 |
| bound prefix | 30/30 | 5/30 | 25 |

Negative-control gate pass means the expected unsafe behavior was reproduced; it is not task success.

## Binding result

The bound policy requires all of: exact prefix content, matching observation sequence, matching binding revision, matching target identity, observation age <= 100 ms, and current focus still on the expected target.

- fresh same-target: **5/5 exact recovery**;
- stale sequence: **5/5 zero-input refusal**;
- stale binding: **5/5 zero-input refusal**;
- wrong target: **5/5 zero-input refusal**;
- expired observation age: **5/5 zero-input refusal**;
- focus changed after observation: **5/5 zero-input refusal**.

The content-only policy accepted all 25 faulty observations because their text still looked like an intent prefix. It failed to complete target A correctly in all 25.

At stop=5:
- stale sequence: observation=`bookk`, current A=`book`; content-only appends `eeperoffice` -> `bookeeperoffice`; bound rejects `stale_sequence` with zero recovery events.
- wrong target: observation comes from B=`bookk` while A=`book`; content-only corrupts A to `bookeeperoffice`; bound rejects `wrong_target`.
- focus changed: observation from A=`bookk`, focus moves to B; content-only sends `eeperoffice` into B while A remains incomplete; bound rejects `focus_mismatch`.

## Controls

- source readback: 7/7 exact Git blob matches before formal execution;
- unit tests: 9/9 PASS;
- all 60 predeclared trial gates PASS;
- every post-trial physical input receipt is empty;
- X keyboard map unchanged;
- final physical input empty;
- model/provider/network calls: 0;
- formal GUI reruns: 0.

Raw formal report: 56,749 bytes, SHA-256 `51017cf28bcfd68390f79a7ebfe2d867bc61a694f24b4263fada67f60657c2ec`. A compressed exact copy is published for reconstruction.

## Interpretation

A text value being an exact prefix is necessary but not sufficient recovery authority. Content must remain bound to a fresh observation of the intended target. Sequence, binding revision, target identity, age and immediate focus are independent fail-closed gates in this fixture.

This does **not** eliminate the observation-to-input race: a target can still change after the final guard and before/during input. It also does not show how a product obtains authoritative application text.

## H/T/D/C/U

**H:** exact prefix content without freshness/identity is unsafe recovery evidence.  
**T:** 60 source-frozen real-X11 trials, two Tk targets, six observation conditions, content-only vs bound-prefix recovery.  
**D:** scoped PASS: bound-prefix recovers fresh 5/5 and zero-input refuses 25/25 stale/identity/focus cases; content-only accepts and fails all 25 fault cases.  
**C:** fixture metadata/text is exact and synchronous; real Office/AX/OCR/DOM observations may be stale, normalized or ambiguous.  
**U:** no atomic transaction, no final-check/input atomicity, no Office transfer, Unicode/IME, Wayland, Windows/macOS, model/token evidence.

## Successor

The next discriminator is a **real application observation transfer** with an independently observable text field. Reuse the same prefix+freshness proof, but make the observation source an application-facing API/structure rather than the fixture's exact IPC. If no reliable observation source exists, recovery must remain refusal rather than infer success from sender receipts.
