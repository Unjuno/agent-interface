# Successor S2 allocation — corrected explicit Docker image argv

This is a new one-shot allocation after predecessor `LABEL-CONTROL-AMBIGUITY-6038-T0-20261002-01` terminated before the candidate process started. Preserve the predecessor STOP unchanged. The only execution correction is explicit placement of image `python:3.12-alpine` between Docker options and process argv. Source, fixture, oracle, policies, cases, and decision gates are unchanged and hash-bound in `FREEZE_v2.json`.

## H / T / D / C / U

**H.** Same frozen hypothesis as T0: on the synthetic layouts, relation-aware current evidence plus abstention preserves the requested field→control effect where geometry/grouping disagree, while abstaining when current permitted evidence is non-unique.

**T.** Allocation `LABEL-CONTROL-AMBIGUITY-6038-T0-S2-20261002-01`, ten cases, three deterministic policies, candidate once, then separate independent auditor once only if candidate exits 0. Candidate container sees only candidate source and visible fixture. Auditor sees only its source, fixture, hidden effect oracle, and candidate raw. Correct command positions explicit `python:3.12-alpine` as image and `python ...` as container command. Network off, root/source/input read-only, CPU/memory/PID bounded, no capabilities, no-new-privileges. Exact identities and argv are in `FREEZE_v2.json` and `results/formal-02/RUN.md`.

**D.** Same frozen method gate: exact reconstruction, correct field effect on seven unique cases, fail-closed abstention on three ambiguous/stale cases, four mutation rejections. Container/launcher failure is typed STOP; a method mismatch is retained FAIL; no retry or substitution.

**C.** The authored fixture may exaggerate visual ambiguity; current trusted relations may be incomplete or wrong; a finite synthetic relation is not a real GUI oracle.

**U.** No real screenshot, GUI, model, user data, app action, privacy/security rate, production safety, or task-effect claim.
