# Issue #57 provider-to-compiled composition R01

## Purpose

Finite synthetic experiment against the frozen current `main`: join one App Server provider usage event to the existing v3 persistent grounding adapter, standard v3 caller, compiled GUI execution, durable allocation receipts, and independent task effect scoring. The negative case changes an intermediate dependency and must yield without issuing the next action.

## Frozen conditions

See `CONDITIONS.json` for the exact base SHA, source hashes, cases, pass criteria, stop rules, and limits. No provider allocation, GUI, WSLc, Docker, or network access is used. The caller receives a fixture coarse candidate, so this run says nothing about cold-path economics.

## Run and custody

`run_experiment.py` runs the single unittest bundle once under Python 3.13.14 normally and once with `-O`. Each process runs one success and one changed-intermediate scenario. It stores raw stdout/stderr/exit bytes and per-scenario protocol, session, provider-call, workspace, and durable-allocation files under `raw/` and `attempts/`. `audit_evidence.py` independently checks joins and custody and writes `AUDIT.json`. Do not rerun against existing output roots; preserve a failed attempt and design a separately numbered packet for any changed experiment.
