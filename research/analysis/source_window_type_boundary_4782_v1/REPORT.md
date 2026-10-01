# Source-window identity type boundary — #4782

Disposition: **HOLD_CALLER_NORMALIZATION_CONTRACT**. This is a six-row pure evaluator contract probe; it is not a GUI revalidation, security regression finding, runtime patch, or production claim.

## H / T / D / C / U

**H.** When `trusted_source_window` is supplied, both the O3 evaluator and its existing source-window verifier compare the string representations of observed and trusted IDs. Therefore a numeric XID and its identical decimal text can compare equal despite distinct input types.

**T.** Six ordered pairs were run once against the exact current-main evaluator and source verifier: int/int same, str/str same, int/str same digits, str/int same digits, int/str with leading zero, and str/int different number. All other evidence fields were fixed valid. The stdlib-only independent auditor checked row order, scalar types, decisions, exact reason codes, strict-typed comparison, and five copied-evidence mutations.

**D.** Candidate and verifier both admitted the two cross-type same-digit pairs; same-type positive controls passed; different spellings/IDs were rejected. Independent audit: 6 rows, errors `[]`, mutation controls 5/5 rejected. Because repository evidence does not establish whether callers must supply one canonical representation, retain HOLD rather than treat coercion as a defect or PASS on a normative contract.

**C.** X11 XIDs are numeric, while JSON or transport layers may represent them as text. A caller may normalize representations before the evaluator. The prior two-GTK-app source-window matrix remains unchanged and passed its own same-representation fixtures.

**U.** No live X11, transport parser, GUI effect, input, model, concurrency, cross-backend identity, or timing was tested. This does not establish an exploitable source-window bypass, actual caller behavior, or a production security claim.

## Provenance and execution

Base main: `43ef66afa8ccc2823d8729093e198e0bf4eef40f`. Frozen evaluator Git blob `50c27bd4e8651da74163c786daeb654928b08958` / SHA-256 `042df7f03687680a0133cfe5ad0a208ec05d5dc27afa7e4e60543560dde9eb1a`; source verifier Git blob `c7bb7b0ea4a7646a0c4208ac4729a68b25a49575` / SHA-256 `182292735cd58f19e5d4a0784194f2c9320efd77cbaa5f6cab24e65f66a66545`. Test/audit/freeze exact Git blobs and source hashes are in `FREEZE.json` and the preformal comment on #4782.

One CPU-only local Docker formal invocation, followed by one separate raw-only audit invocation. Cached Python 3.12 slim Bookworm image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64, network disabled, read-only root/source, one CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. No GPU, model, external service, package install, or GUI.

Runner exit 0; audit exit 0. Raw SHA-256: `bf79713bf44a12c49ba7283b39d583ac264b79c416ffba4beab644cb759ed1dc`. Formal reruns/replacements/tuning: 0/0/0. Two excluded preformal construction defects are disclosed on the Issue; neither invoked the candidate.

No runtime or shared research implementation was changed. The result does not reopen or supersede #3215/#3224.
