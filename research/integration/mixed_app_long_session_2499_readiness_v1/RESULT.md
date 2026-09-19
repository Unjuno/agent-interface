# #2937 readiness guard result

Date: 2026-09-20

Decision: `PASS_FAIL_CLOSED_READINESS_CONTRACT`

Local pinned Docker run (`python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`,
`--network none`, read-only source) ran four cases:

- missing identity: refused before geometry
- auxiliary-only identity: refused before input
- multiple main identities: refused
- exactly one main identity: admitted with bound window id

All four tests passed. This is a readiness contract result only. It does not
claim that the live formal runner has been repaired or that #2499 acceptance
has been achieved.
