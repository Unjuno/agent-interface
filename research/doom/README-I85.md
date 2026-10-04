# I85 producer/analyzer cross-layer construction test

This package composes the exact producer and consumer source snapshots listed in `FREEZE-I85.json` against an eight-case preregistered synthetic matrix in `raw-cases.json`. The candidate is run once; `audit_cross_layer_I85.py` independently checks the saved output without importing either implementation.

This is CPU-only construction evidence. It uses deterministic synthetic backend/owner fixtures, makes no live X11/MAP01 observation, consumes no formal allocation, and cannot satisfy Issue #59 live threat-exposure/useful-feedback requirements.

Reproduce from this directory using the exact commands in the freeze record. Candidate and audit stdout are preserved in their respective `*-I85.json` files.
