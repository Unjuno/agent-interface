# Focused observation request successor #1998

## Scope

This additive analytical fixture tests only request validation and exact focused evidence reconstruction. It does not call a model, GUI, network, runtime, or input API.

## Frozen allocation

- branch: `research/focused-observation-request-successor-1935`
- path: `research/analysis/focused_observation_request_successor_1935_v1/`
- source: current `main` at allocation time
- implementation: standard-library Python
- rows: 256 finite frame/request combinations
- local result: 16 valid focused requests, 240 fail-closed requests
- result SHA-256: `5c2699e993fd163a1a01c72c3905b46c8f364e329a8ddef47c37bb713952b936`

## Decision

The construction passes its narrow oracle: valid requests require matching epoch/identity, an explicit uncertainty reason, and in-bounds regions; all other requests are rejected. This is not yet a retained formal result because an independent audit and GitHub PR are still required.

## Stop boundary

Do not infer model usability, token/latency savings, automatic region discovery, GUI correctness, authority, or cross-domain transfer.
