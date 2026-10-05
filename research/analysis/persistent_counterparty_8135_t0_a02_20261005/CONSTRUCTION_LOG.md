# A02 construction record

- Intake: Issue #8135 T0 only; GitHub search found no branch or PR mentioning
  8135 at intake. No T1/GUI allocation is requested or inferred.
- A01's frozen single candidate/auditor pair failed because the auditor expected
  episode field set omitted `arm`; that raw outcome is immutable in A01.
- The finite design crosses five counterparty controls, two route orders, two
  public seed histories and two sham assignment slots (40 blocks, 80 episodes).
- The counterparty selector receives only a prior public event, a sealed
  frequency-sham assignment, or a constant/reset input depending on arm. Truth
  is stored separately and is not mounted into the candidate container.
- Fresh deterministic shuffle seed: `20261006`. Candidate rows are proposals only. The independent auditor adjudicates
  synthetic effects under a fixed hard gate; no external effect is attempted.
- OrbStack image is pinned to the already cached Linux/arm64 Python 3.14.8
  digest. No image pull, model, network, service, or user data is involved.
