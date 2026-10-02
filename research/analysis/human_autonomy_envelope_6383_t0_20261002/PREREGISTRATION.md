# Issue #6383 T0 preregistration

## H / T / D / C / U

**H.** An observation-only autonomy-envelope renderer can report the current
state, permitted next action classes, target scope, evidence generation and
expiry, revocation trigger, and physical-release state without asserting a
permission or terminal outcome that current receipts do not support.

**T.** Run a finite, no-model, no-GUI fixture of ten frozen checkpoints. The
candidate reads only source receipts and emits a source-bound display record.
An independently written auditor derives the expected record from the raw
fixture; it must not import or execute candidate code. Construction controls
mutate action scope, stale generations, lease expiry, release proof, terminal
obligations, source identity, row cardinality, and source binding. Run one
candidate and one separate raw-only CPU audit in WSLc, with network disabled,
source mounted read-only, no GPU, and unique output. No retries.

**D.** `METHOD_PASS_SCOPED` only if all ten checkpoints independently
reconstruct exactly, each visible claim is receipt-entailed, stale/expired or
revoked authority yields no permitted actions, unverified release is never
shown as verified, terminal state requires every frozen obligation, the
source digest matches, and every frozen corruption control is rejected.
Otherwise preserve `FAIL_METHOD` or `HOLD_INTEGRITY`. This rung cannot establish
human comprehension or operational benefit.

**C.** Deterministic synthetic receipts and one renderer/auditor implementation
may not represent runtime receipt latency, actual GUI state, or varied human
interpretation. Simpler “working/stopped” cues may be more usable.

**U.** No human participants, GUI, model, input, or live authority path is
tested. Passing proves only bounded display fidelity for these ten fixtures;
it does not establish that people predict the envelope, act at the right time,
or benefit from a richer display. T1 requires separately approved voluntary
research and is not included here.

## Frozen execution contract

- Source: this additive package at `research/analysis/human_autonomy_envelope_6383_t0_20261002/`.
- Fixture: `fixture.json`, ten checkpoints; no generated or hidden fields.
- Candidate: `candidate.py`, one invocation, reads fixture and writes one JSON result.
- Auditor: `audit.py`, one invocation after candidate exit 0; reads only fixture and candidate output, writes one JSON audit.
- Construction tests: `test_contract.py`; they do not count as candidate or audit invocations.
- Runtime: cached digest-pinned PyTorch linux/amd64 image via `wslc.exe`; `--pull=never --network none --gpus` omitted; source read-only; candidate and auditor in separate ephemeral containers.
- Formal candidates=1 maximum; independent audits=1 maximum; retries=0. Any source/input/image/runtime change, output collision, failed invocation, or missing output terminates this allocation.
