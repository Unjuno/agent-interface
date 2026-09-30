# Source freeze — Issue #5404 T0

Frozen at `2026-09-30T10:38:13Z` UTC, before the formal allocation.

- Base/main and local HEAD: `e81cbac968752791678d22a4de3f2d276497d614`
- `PLAN.md` SHA-256: `2b0290232abbb9494392a0f3ca5c15fa010706fea596da84b9a97d647a2d82ae`
- `experiment.py` SHA-256: `c1aa98f922acbdf2ca2d37dac24ef23be145d5ea9ed7a887fc964dada188daeb`
- `audit.py` SHA-256: `8ec413da90329acb4a606d51c58dd3257e228d30c6590aadbb686d0fab4a24c5`
- Docker context: `orbstack`, Engine `29.4.0`, endpoint `unix:///Users/taka/.orbstack/run/docker.sock`
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; read-back `linux/arm64`
- Local `docker ps` was empty at freeze; no active container was observed.

Candidate and auditor source are immutable for the formal allocation. A pre-freeze construction smoke is not the formal result and its scratch raw files were not retained.
