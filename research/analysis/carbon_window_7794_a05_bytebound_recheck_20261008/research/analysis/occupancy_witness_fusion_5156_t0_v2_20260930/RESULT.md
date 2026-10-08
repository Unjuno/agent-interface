# T0 v2 result — owner-release / server-witness interval fusion

Decision: **`PASS_INTERVAL_FUSION_CONSTRUCTION_ONLY`**.

## H / T / D / C / U

**H.** Under a common monotonic clock, matching owner/actuation/key/display
identity, one release, and no re-press, intersecting the independent server
state witness interval with the owner KeyRelease/XSync bracket preserves every
compatible logical key-up time while potentially narrowing the feasible set.

**T.** Source freeze: base/current main
`79e7c9af7e7fa3371f5ca3994c6b72e6cdb8456c`; CPython 3.12.10 on the Windows
host; Python standard library only. One candidate invocation enumerated every
pair of DOWN/UP query intervals over integer time 0..4 against every ordered
owner request-start/request-return/XSync-return triple over the same domain.
The raw contains 7,875 valid finite-domain cases and 14 malformed/corruption
controls. A separate raw-only auditor enumerated compatible hidden DOWN
snapshot, release, and UP snapshot times without importing the candidate.

**D.** The independent audit checked 7,889 rows with `errors=[]`. Candidate
interval sets exactly matched the oracle's feasible hidden-release sets; no
compatible discrete time was omitted. All malformed, identity-mismatched,
transition-invalid, and empty-intersection cases stayed `UNKNOWN`; authority
was false. In 586 valid cases, the fused interval was strictly narrower than
both the witness-only interval and owner-only bracket. Result and audit hashes
are retained in `RUN.json`.

**C.** This is a synthetic discrete-time contract experiment. It assumes exact
clock comparability, a single server incarnation, a single DOWN-to-UP
transition, no re-press, and that XSync return bounds processing of the prior
release request. The auditor is separately implemented but same-author; it is
not independent human review. The old attempt 01, stopped before runner import
because main advanced after freeze, is preserved under `predecessor_attempt_01/`.

**U.** No X11, XTest, actual key hold, GUI input, MAP01, model, task effect,
recovery efficacy, safety rate, human tempo, or non-DOOM runtime transfer was
measured. Docker/OrbStack was not invoked because #5085 has no exact assignment.
This result does not satisfy #5156's empirical X11 gate and does not certify a
physical release timestamp. The still-unspent #5156 fixture measurement must
be separately assigned and freshly frozen before execution.

## Reproduction and artifacts

The construction suite was run once before freeze and once after the formal
T0 runner/audit. From this directory, the non-consuming test command is:

```powershell
python -B -m unittest -v test_fusion.py
```

The candidate and auditor each ran exactly once; their outputs already exist.
Do **not** rerun them under this identity. Exact invocations, exit codes,
source hashes, and output hashes are in `RUN.json` and `FREEZE.json`. Any
further experiment requires a separate allocation identity.
