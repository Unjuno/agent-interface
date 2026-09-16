# Source-first freeze — mandatory mediated reads

Task: `COORD-MANDATORY-READ-CAPABILITY-20260917-020`
Issue: #523
Publication base: `8e0db289c75beafe6c62fba0d55aa13cbe75c253`

Single factor: raw authoritative SQLite capability available to task process (`unrestricted`) versus removed by Linux UID/filesystem separation (`mediated`). Same task code deliberately attempts direct B read first; only on denial does it use the receipt-producing Unix-socket capability.

Formal allocation: 12 fresh first outcomes, fixed `plan.json`, no retry/replacement/extension/tuning. Owner revision validation and generation commit occur in one SQLite `BEGIN IMMEDIATE` transaction. Construction outcomes are excluded.
