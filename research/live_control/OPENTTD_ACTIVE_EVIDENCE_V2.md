# Model-proposed OpenTTD active evidence v1/v2

Status: retain the v1 failure and the v2 screen-derived candidate. This is one
OpenTTD toolbar task, not a general grounding or speed result.

## Question

Can one planner model open a held-out OpenTTD toolbar window without a
caller-supplied answer coordinate? The interface must treat model confidence and
candidate points as proposals only, collect semantic evidence from the live UI,
and admit the target click only after the model binds its selection to verified
evidence.

The planner is Luna-low for every model call. No subagent participates in target
proposal, evidence interpretation or action selection. Deterministic local code
checks the screen structure, evidence persistence, focus/surface binding, input
release and independent task effect. Moving work to another model or agent is not
counted as token reduction.

## Contract

The first call receives the full source frame and returns exactly three coarse
toolbar points. Its `visually_unambiguous` field grants no input authority. The
runtime moves to candidate points, waits 800ms, captures the tooltip and observes
again. A receipt is valid only when the same tooltip pixels persist, focus and
surface binding remain equal, and pointer admissions exactly match the proposed
points. The second call sees the source frame and numbered tooltip strips and
may select only a point bound to one receipt. The selected receipt is rehovered
and compared exactly before ordinary input admission.

Success is an exact fixed-seed RGB digest of the visible company-finances title,
computed outside the model path. Program completion and the unrelated road-task
driver score do not count as this task's success.

## Retained v1 failure

The preregistered v1 pair probes only the first model's three free-form points.
Its association-fault case reverses the point/receipt mapping and correctly
refuses before the second model call and target click. In the stable case the
first model self-reports `visually_unambiguous`, chooses `[436,51]`, and proposes
`[436,51]`, `[412,51]`, `[460,51]`. The finances control is absent. After three
valid hovers, the second call selects `[460,51]`; the click completes and releases,
but the independent finances oracle is false. Decision start to independent
evaluation is 44.724s. Inputs are 9,296 and 9,795 reported tokens. The pair is
retained as `HOLD_AND_PRESERVE_ACTIVE_EVIDENCE_PAIR`.

This falsifies two assumptions: self-reported confidence cannot authorize a
click, and an unconstrained three-point model proposal does not guarantee useful
candidate coverage.

## Screen-derived v2 repair

V2 detects 30 repeated 22px toolbar slots directly from exact source pixels. It
uses the model's direct point as a coarse anchor, or the median-x candidate when
the model requests probing, and takes the anchor slot plus two neighbors on each
side. This produces five meaning-free points:

```text
[389,51] [412,51] [435,51] [458,51] [485,51]
```

The runtime's 3,000ms aggregate passive-dwell limit rejects five hovers in one
program. V2 preserves that limit and uses batches of three and two points. Batch
receipts compose only when their exact binding agrees. A development attempt
that exceeded the dwell bound and a later over-wide span attempt both stopped
before target input; their local artifacts remain unpromoted.

The preregistered v2 association-fault case performs all five hovers, then
reverses the first batch's claimed association. Composition refuses before the
second model call and admits zero target pointer input. The independent finances
oracle is false.

The stable case collects five receipts in two batches. The same Luna-low planner
selects receipt 5 at `[485,51]`, whose visible tooltip identifies company finances.
An exact rehover matches the original tooltip receipt. Ordinary pointer admission
then clicks the point, verifies release, and the independent title oracle passes.
The candidate and evidence calls report 9,296 and 10,178 input tokens. The two
hover batches take 6.400s; decision start to independent evaluation takes
33.920s. The lower total time than the failed v1 case comes from different sampled
model wait and is not a speedup claim.

## Audit and scope

`audit_openttd_active_evidence_v2.py` rechecks both preregistrations and source
hashes, parses raw model events, reconstructs the contracts and receipts,
recomputes slot discovery and the independent oracle, verifies every terminal
release and reconstructs every `.ait` frame. It passes on Windows and WSL across
126 exact frames: v1 fault/stable 24/33 and v2 fault/stable 30/39.

The evidence supports one candidate: coarse model grounding can be combined with
screen-derived repeated-control geometry and active semantic evidence. It does
not support broad unknown-app grounding, a general toolbar detector, token
reduction, causal latency improvement or human operating tempo. The next test
should change toolbar layout or application while preserving the same
proposal/evidence/receipt boundary, then reduce five serial 800ms probes without
removing persistent semantic evidence.
