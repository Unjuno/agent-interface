# Issue #6405 T0 freeze — approval sequence assay

Frozen: 2026-10-02 01:39:46 UTC

Allocation: `APPROVAL-SEQUENCE-ASSAY-6405-T0-20261002-01`

Base: `d0e2a0f7b10bd3eecf4741f045e90d15ee43e3ad` (`origin/main`)

Branch: `research/approval-sequence-assay-6405-t0-20261002`

Outputs: `results/formal-01/candidate.json` and `audit.json` (both must be absent)

## H / T / D / C / U

**H.** A finite renderer can present the same five authored approval requests
under static, changed-field-salience, and narrowly eligible batching arms while
preserving every request field, explicit scope/expiry, deny/cancel choices and
exact request-digest authority binding. The experiment does not predict human
discrimination.

**T.** One fixed sequence contains two repeated nonconsequential label requests,
a consequential recipient/effect change, a separate valid consequential save,
and a late scope change. The candidate emits all three display arms once. A
separately implemented raw-only auditor reconstructs the display truth and
executes six in-memory corruptions. Candidate invocations: one formal maximum;
auditor invocations: one formal maximum after candidate exit 0; retry budget: 0;
participants, live approvals and external effects: 0.

**D.** `PASS_METHOD_SCOPED` requires (1) exact five-request coverage/order in
all arms, (2) all principal/target/recipient/effect/scope/expiry/consequence
fields visible and equal to fixture truth, (3) changed-field highlights exactly
match target/recipient/effect/scope differences from the preceding request,
(4) only nonconsequential requests may share a batch and each retains its own
scope, expiry and approve/deny/cancel controls, (5) an r1 receipt is refused
against changed r3 by exact digest mismatch, (6) denial and cancellation remain
separately represented, and (7) all six mutations are rejected: omitted
recipient, swapped recipient, stale highlight, overbroad consequential batch,
stale receipt reuse, and erased deny/cancel choice. Any baseline error or
mutation acceptance is `FAIL_METHOD_CONSTRUCTION`.

**C.** Authored fixture truth, deterministic serialization and the independent
auditor are the oracle boundary. Candidate and auditor are separate code paths,
but share the published field contract and fixture. The five requests are
hand-authored and do not model a population or estimate a base rate.

**U.** No human participants, attention/comprehension endpoint, habituation,
false-approve/false-deny rate, burden, trusted UI, broker implementation,
real authorization, security behavior or production transfer is tested. No
batch policy is recommended by this T0.

## Frozen bytes

| Artifact | SHA-256 |
|---|---|
| `candidate.py` | `a8c120fea9a8879ced6df061032b208f6597d6231fa6f828073cbc6ba2e22331` |
| `audit.py` | `b0819aaec92e509b2ee5577e4d61fcf09639bcf9e5158057e05f50085d6db041` |
| `fixtures/sequence.json` | `92b8c58507bcefae6fb43f1583b4257a43957c73f0e64da907a214a70a923c6b` |
| `test_construction.py` | `cca51497fe2a58479aab33567cd66d22c564267de3d92cdc46d4b3d0aa7aae15` |
| `test_audit_construction.py` | `60945d22c701aefeab170d5be25730a37ee1de8c9328ffb4d4d1e33a797a0991` |

Construction suite passed 8/8 before freeze; Python byte-compilation passed.
Environment: macOS arm64, CPython 3.14.5. `wslc.exe` is not available in
this task environment. OrbStack currently has unrelated container
`unjuno-native-ci-6092` running (observed, not modified); no exclusive
container CPU lane is assigned. Because this is a deterministic finite fixture
with no OS/container semantics, the formal candidate/auditor will run once on
the host. This is an explicit WSLc-preference deviation, not container evidence
or a resource-enforcement claim. No Docker command is part of the formal run.

## Formal commands (single-use)

Run only if the exact base/head and frozen byte hashes remain unchanged and
both output files are absent:

```sh
mkdir -p results/formal-01
python3 candidate.py --input fixtures/sequence.json --output results/formal-01/candidate.json
python3 audit.py --input fixtures/sequence.json --candidate results/formal-01/candidate.json --output results/formal-01/audit.json
```

Candidate must exit 0 before the auditor is invoked. Do not rerun either
formal command. Preserve stdout, stderr, exit codes and output hashes. A failed
formal gate is retained as-is and reported on Issue #6405.
