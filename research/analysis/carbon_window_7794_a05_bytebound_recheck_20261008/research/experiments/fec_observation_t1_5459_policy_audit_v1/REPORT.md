# #5459 T1 independent arm-policy schedule audit

## H / T / D / C / U

**H.** An independent reconstruction of the frozen retransmit/fixed/adaptive
send policies will match every arm schedule in the immutable T1 raw bundle;
mutating a follow-up into another arm's behavior will be rejected.

**T.** Audited PR #5484 head `7e7c5e072985fe14f4e647381e6265c1307fe00e`
without importing its candidate simulator or decoder. The input was the exact
Git blob `15c3e84d7295fe68f840b60487e06e460aa4fb40` at
`research/experiments/fec_observation_t1_5459_20260930/results/t1-01/raw.json`.
The audit independently reconstructed initial source slots, feedback-cut
availability, and each arm's expected follow-up packet type, identity, mask,
label, and send round. It checked all 1,536 trace rows and 15 fault rows.
Seven unit tests cover fixed repair, retransmission, adaptive pair repair,
clean-window overhead behavior, and two wrong-policy mutations.

**D.** `PASS_POLICY_SCHEDULE_SCOPED`: 1,551 rows checked, zero policy
mismatches. The raw file was 3,852,712 bytes and SHA-256
`1AD1B1037ACA9496E8617CCF70AA2F23B7E373C7754002DCF3100BF0D9EDDF6E`,
matching the SHA recorded in the original T1 `RUN.json` / `AUDIT.json`.
`python -B -m unittest -v test_policy.py`: 7/7 passed.
`python -B audit_policy.py raw.json`: exit 0, no mismatches.

**C.** Local Windows CPython host-only posthoc audit of pinned GitHub bytes;
no Docker, model, GPU, CUDA, GUI, or candidate rerun. This add-on does not
alter the original T1 raw/result. The independent policy check is separate
from the original PR auditor, which still does not verify arm-specific send
schedules on arbitrary mutated raw input.

**U.** A deterministic XOR fixture does not establish behavior or benefit for
real transports, RaptorQ, or observation delivery. This audit confirms only
that the published T1 raw follows the preregistered arm schedules; it does not
upgrade T1 to a real-transport result or close #5459.

## Source hashes

- `audit_policy.py`: `6A0105A18D1120694300323CBDA4C139E8B05EBA18935A535AB1C20DE8B00439`
- `test_policy.py`: `FAD9680D72023AB54061EF804C92BC05096B66116202F19EBF1DD4E3CAC8BD16`

