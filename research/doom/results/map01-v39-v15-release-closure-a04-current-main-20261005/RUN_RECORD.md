H/T/D/C/U: see README.md. A04 is a current-main static import-closure successor, not a candidate or formal run.

Source: origin/main c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d.
Commands (repository root):
1. `python -B research/doom/results/map01-v39-v15-release-closure-a04-current-main-20261005/derive_current_closure.py`
2. `python -B research/doom/results/map01-v39-v15-release-closure-a04-current-main-20261005/audit_current_closure.py`

Both exit 0. Each emits `PASS_STATIC_IMPORT_CLOSURE`; 38 source files, unresolved=0, external imports PIL,Xlib,numpy,vizdoom. Independent manifest/blob audit: 38/38 source blob SHA-1 and content SHA-256 match. A03-to-A04 source comparison: 0 changed, 0 added, 0 removed blobs. Mutation controls reject wrong source SHA and altered blob identity. `py_compile` passes on both scripts.

No candidate/production import, container, display/game, model, or input was used. WSLc list was empty; host disk was about 1.4 GB free. No formal allocation consumed.
