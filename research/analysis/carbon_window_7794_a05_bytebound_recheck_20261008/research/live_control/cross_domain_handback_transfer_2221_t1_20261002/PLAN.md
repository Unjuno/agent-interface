# Cross-domain retained-evidence handback T1 — source transfer candidate

Issue lineage: open #2221 (live/model-facing successor) and closed #1530
(retained-evidence HOLD). This T1 is a model-free preparation experiment on
newly selected retained evidence, not a substitute for #2221 acceptance.

## H / T / D / C / U

- **H:** One provenance-bound, non-authoritative evidence envelope can retain
  semantically distinct DOOM/MAP01 and browser-desktop records without
  promoting viewport change to useful task effect, physical release to task
  completion, or an exact server-side submission to visual acknowledgement.
- **T:** Read only the hash-pinned r133 MAP01 v38/v39 analysis and public
  comparison04 task-6 independent visual/provenance audit. Produce four cases:
  v38 first exact plan frame; v39 three first exact plan frames plus separate
  health-revocation physical-release record; direct browser task-6 submission.
  Run a candidate and a separate raw-only auditor. Exercise corruption controls
  for effect promotion, release relabeling, missing visual acknowledgement,
  source-lineage forgery, clock joining and authority expansion.
- **D:** `PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED` only if all frozen source
  hashes match; 4/4 case identities/lineages match independent retained
  records; every DOOM viewport receipt remains `OBSERVED_CHANGE` with task
  effect `UNRESOLVED`; kill/no-exit and verified release remain distinct; the
  browser exact-once submission is retained as task effect while visual
  acknowledgement remains `UNKNOWN_NOT_OBSERVED`; mutations fail closed; no
  authority or cross-source clock join is introduced.
- **C:** A two-domain retained-source candidate says nothing about the live
  #2221 requirement for model recovery on actual routes. DOOM's kill is only a
  domain progress outcome, not MAP01 completion. The browser archive is one
  serial cooperative pair, and its direct task-6 acknowledgement is visually
  incomplete. No causal latency/cross-clock conclusion is allowed.
- **U:** Whether a model safely chooses DONE/WAIT/QUERY/RETRY/ABORT under these
  typed outcomes; whether the envelope transfers to held-out live routes;
  whether any task value, recovery, latency, cost or human-tempo changes.

## Source / stopping boundary

Base is main `9ccad4d889168e5d40933c8d03d76dc4d1cdd26a`. Inputs and blob/SHA256
identities are in `SOURCE_HASHES.json`. Existing v38/v39, browser comparison04,
and #2221 v1 records are read-only. No historical model/game/GUI/input
allocation is rerun. Docker Engine was confirmed stopped; no service start or
container is attempted. Candidate and raw-only audit are each allowed once
after the source freeze; deterministic construction tests are outside that
one-shot pair.
