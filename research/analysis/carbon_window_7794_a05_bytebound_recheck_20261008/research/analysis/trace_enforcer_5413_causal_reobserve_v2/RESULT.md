# Issue #5413 successor T1 — reordered stale responses

Allocation: `trace-causal-reobserve-5413-20261001-02`  
Frozen source main: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`  
Publication branch was created from current main `3befc5fb720e8d8aed3f6e6f3e6e881c42070f8e`; this later publication base does not change the frozen experiment inputs.  
Disposition: `PASS_CAUSAL_REOBSERVE_DELAY_BOUNDARY_CONSTRUCTION_ONLY`.

## H / T / D / C / U

- **H:** When invalidation supersedes a pending reobserve request, delayed responses from the prior generation must not clear current stale state or admit an action. A matching response for the newest request/generation with sequence strictly newer than its baseline may restore admission; polling while pending must not duplicate requests.
- **T:** Exhaustively enumerate all traces of length 0–6 over the fixed seven-event alphabet (137,257 total), stream raw candidate transcripts as gzip JSONL, run one eight-test suite, one candidate, then one independent raw-only streaming auditor with five mutations.
- **D:** Tests 8/8. Candidate emitted 137,257 rows. Independent oracle matched all 137,257 rows with `errors=[]`; the five corruption controls (stale action, unlinked response, superseded response, duplicate request, changed trace) were all rejected. Disposition is scoped to the frozen finite bookkeeping model.
- **C:** CPython 3.11.9 host CPU, standard library. Synthetic request IDs, generations and observation sequences are trusted labels. No live display, capture channel, clock, game, model, GUI, or external effect.
- **U:** No deadline or capture authenticity guarantee, useful-feedback timing, real-time control benefit, or production safety claim. This does not close #5413 or #59 and does not justify a runtime behavior change.

The compressed raw is preserved as UTF-8 base64 chunks under `raw.jsonl.gz.b64.parts/`; concatenate parts in lexical order, decode base64, then gunzip. `RAW_PACKAGE.md` gives the exact reconstruction procedure and independent size/digest checks. `RUN_LOG.md`, `AUDIT.json`, `FREEZE.json` and `SHA256SUMS.txt` retain command receipts, lineage and hashes. No Docker lane was used because #5085 has no assignment for this CPU-only analysis; no GPU or model training is relevant to the finite discrete-state test.
