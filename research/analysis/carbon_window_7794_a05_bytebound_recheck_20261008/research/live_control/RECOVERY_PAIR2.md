# Registered pair 2 — three fewer recovery orchestration calls

Pair 2 completed the registered Inkscape seed-202 B-then-A order. The measured
`recovery_pair2_v1.py` runner stayed identical across both arms; pair 1's measured
runner and result were not altered. Both tasks completed on their first move/save
program with matching saved results.

| Outcome | A: separate reads | B: helper |
|---|---:|---:|
| Recovery orchestration calls | 4 | 1 |
| Recovery socket reads | 4 | 4 |
| Total socket exchanges | 14 | 14 |
| Exact observation frames | 9 | 9 |
| Capture to evaluation | 92.787 s | 59.039 s |

The observed recovery-call difference is B-minus-A = **-3**, while socket reads
are unchanged. This meets the registered exploratory call-count threshold for
this one depth-3 pair. It does not establish a generalized model-performance gain.
The full elapsed difference is -33.748 s; A includes repeated history/image review
and a progress commentary between reads 3 and 4. These times are retained rather
than adjusted. Exact model identity/configuration and receipt timestamps are still
unavailable, so the plan's model-performance qualification is not met. The two
arms also ran in different continuation turns; same exact model configuration
cannot be inferred from the same generic model-family description.

The protocol's depth-3 prose specifies **three additional historical clock
boundaries before the own clock**. The runner records that literally: after an
observe-only advance, it issues and receives three explicit setup clocks, then
deliberately invokes the stale initial batch. That stale attempt returns the
earliest clock boundary and stops without submitting its Right hold. Recovery
therefore requires four additional reads: three historical boundaries plus the
own clock. The pre-query execution metadata states both numbers. This is not a
claim that depth 3 means three total reads; retain actual counts in comparison.

B's frozen reader traversed these four received slices in one orchestration call.
The assistant received the complete assembled history and original image together,
reviewed it, then explicitly submitted the registered move/save steps. The program
completed without interruption. The independent legacy score and saved SVG agree
on x=52, y=50, width=40, height=30, transform absent. This is a rightward-motion
contract, not a requested-distance precision result.

## Verified B evidence

- Four read-only recovery exchanges, with no command field in any read request.
- Each of the first three recovery boundaries equals its recorded setup clock;
  the fourth contains the original stale attempt's own request identity.
- The assembled actual history is exactly the later move caller's source batch.
- Fourteen total socket exchanges cover all 47 unique raw events, including overlap.
- Nine exact AIT/PNG frames, pinned sources, completed terminals and input release,
  and independently saved SVG fields pass the audit.
- Capture-to-evaluation duration: **59.039201361 seconds**.

Bridge exit zero and the combined history/image experience are recorded in the
conversation-derived presentation metadata. As before, this old entry provides
no structured per-child cleanup artifact. Exact model identity/configuration,
model receipt times and actual token/cost accounting remain unavailable, so model
performance qualification is not met. Grouping four network reads into one model
call does not eliminate those network reads.

## Paired verification and remaining work

The new paired audit verifies both arms' source hashes, identical initial PNG and
move steps, all 94 unique raw events and received slices, all 18 AIT/PNG frames,
every intermediate A assembled history, and own-clock identity at the final read.
It also checks the assembled batch actually used for move and the independent
saved SVG fields. A's four recovery stages were separate model tool calls, each
displaying the current history and original image. Those presentation boundaries
are conversation evidence; runtime timestamps alone cannot prove model receipt.
Both bridge handles returned zero and neither arm needed an extra move retry.

Study progress is **4 of 8 episodes**, with four remaining. Next execute pair 3,
OpenTTD depth 1, B then A. Retain the original B-only audit as historical evidence;
the paired audit is an additional artifact, not a replacement. Do not rerun either
arm to improve the observed numbers. Across-domain and completed-study conclusions
remain pending.

```sh
python3 research/live_control/audit_recovery_pair2_b_v1.py
python3 research/live_control/audit_recovery_pair2_v1.py
```
