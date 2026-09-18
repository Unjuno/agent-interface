# #1688 Report — live phase overlap on two X11 surfaces

**Decision: `PASS_LIVE_PHASE_OVERLAP_X11_SCOPED`.**

## Question
Does one serialized ordinary X11 keyboard require whole-intent serialization, or can input on surface B begin while surface A's already-triggered application effect is still pending?

## H/T/D/C/U
The preregistered H/T/D/C/U are retained in `PLAN.md` and Issue #1688. The formal block used four arms x six fresh first outcomes under private Xvfb sessions, one XTEST core keyboard, 150 ms delayed effects, and an independent server-pixel scorer.

The negative arm deliberately makes both tails depend on one shared X-server root property. It is not a candidate optimization; it tests whether hidden global state invalidates surface-only independence.

## Formal first result

| arm | n | exact expected visible effect | median wall ms | terminal Space neutral |
|---|---:|---:|---:|---:|
| serial_independent | 6 | 6/6 | 303.290324 | 6/6 |
| overlap_independent | 6 | 6/6 | 152.974366 | 6/6 |
| serial_shared | 6 | 6/6 | 303.623415 | 6/6 |
| overlap_shared negative | 6 | 6/6 preregistered contamination detected | 153.5249835 | 6/6 |

For the independent pair:
- median reduction: **150.315958 ms**;
- overlap/serial median ratio: **0.5043826126**;
- preregistered gates were reduction >=100 ms and ratio <=0.65.

All 24 cases had exactly one observed KeyPress on A and one on B. In every overlap case, B KeyPress preceded A effect; in every serial case, A effect preceded B KeyPress.

Tail timing remained close to the controlled 150 ms fixture value. Independent overlap A/B effect delays were approximately 150.37–150.86 ms and 150.34–150.95 ms; serial independent delays were approximately 150.12–150.90 ms and 150.31–151.85 ms.

## Negative shared-resource result
The overlap-shared arm is the important safety control. Both surfaces write one shared X-server root property when their input is consumed; each delayed tail later reads that property.

In all 6 unsafe overlap cases:
- A wrote `A`;
- B wrote `B` before A's delayed read;
- A therefore read `B` and rendered blue instead of red;
- B also rendered blue;
- the independent pixel scorer observed A=[0,0,255], B=[0,0,255] and rejected A correctness.

The serial-shared arm was 6/6 correct because A's tail read completed before B overwrote the shared resource.

This directly rejects a scheduler that treats `surface_id` alone as an independence proof.

## Interpretation
#1670's abstract result transfers to a real X11 input/effect timing boundary under the frozen fixture: one globally serialized actuator does **not** require serializing unrelated effect-pending/verification tails. The safe unit of exclusivity is the resource-using phase, not necessarily the whole intent.

However, phase overlap is admissible only when tail resources and dependencies are explicit. Hidden global state can make the faster schedule incorrect even though input itself is perfectly serialized and each target surface is distinct.

A runtime concurrency contract therefore needs at least:
1. phase identity (`INPUT`, `EFFECT_PENDING`, `VERIFY`, cleanup/handback);
2. exclusive actuator/focus resources for input;
3. declared tail read/write/global resources;
4. dependency edges when later input requires earlier effect knowledge;
5. fail-closed serialization for unknown resources;
6. per-intent effect verification and neutral-input evidence.

## Integrity
Frozen pre-formal SHA-256 values:
- `PLAN.md` `89bc2d4f5982e2c911243f693af5c76b52b083d712d73486e4ed61b81bb8e1a8`
- `run_case.py` `d07cdb5fe17079654714414c489069c7370b42c2eb7266feb2bbf70d83f0a0f8`
- `run_formal.py` `2c4ef5dff577d9eaea06d8fc1d508e9ca04074c0c672129b07a9f7a9d74b742f`
- `audit.py` `c26ee19922eab5dac2c94b8c158abf2609dbc11f83daad5b4a3f0bf443ce0034`
- `schedule.json` `0b26f4657c9c45e52d2425b23704d2ddff2d57b5d9ddc65e2aa51e2c0dae5e89`
- `prereg.json` `67049828e70cbe48fe80d5fd192ca2f98b903da2e1ccbfb492df8677f21f310a`
- `environment.json` `ba526382cc9636c34fcc292002e39335fe69259bcb4eb6959483c1b872000885`

Formal invocation count 1, reruns 0, tuning after freeze 0. Independent audit decision: `PASS_LIVE_PHASE_OVERLAP_X11_SCOPED`, errors `[]`.

Postformal output hashes:
- `RAW_CASES.json` `8dc12b19e94b0cbd20e169073272fc3a512fef3ee66100360e2f6f30656badd5`
- `RESULT.json` `fae8422566697bf532dd9b576ba06b5b96449754413d377f216594a5c5c5003a`
- `AUDIT.json` `6938c6e02467e47f01b454728a741ee2e650e57b4db0d44b548cd0d821da029b`

GitHub retains the 46,325-byte raw ledger losslessly as deterministic gzip+base64 `RAW_CASES.json.gz.b64` because the conversation write path is text-oriented. `restore_raw.py` decodes it and refuses unless the reconstructed `RAW_CASES.json` SHA-256 is exactly `8dc12b19e94b0cbd20e169073272fc3a512fef3ee66100360e2f6f30656badd5`. The deterministic gzip SHA-256 is `2036610150d8702d9ba8fedd41943559e2c8021c1eafdd4c684d464f8e993b42`.

## Construction exclusions
Pre-formal setup failures remain excluded and are described verbatim in Issue #1688: missing default Xauthority, Tk/XTEST delivery mismatch, one cross-thread Display ownership timeout, and Python-Xlib str/bytes normalization. No formal ID was used during those repairs.

## Next rung
Transfer only the proven scheduling shape, not the synthetic timing value, to a real application pair. The smallest useful successor is two independently scored real GUI effects where at least one effect has a naturally pending interval after input release. Compare whole-intent serial versus phase overlap with a matched hidden-global conflict control. Do not add a second physical pointer unless the real task actually requires actuator parallelism.

## Limits
Linux/Xvfb/XTEST, synthetic windows and controlled 150 ms tails. The shared root property is a controlled stand-in for clipboard/global mode. No model/token/human-tempo, cross-platform, real-productivity-app, or production-runtime claim.
