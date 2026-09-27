# Issue #2907 — independent stale observation and binding construction05

## H/T/D/C/U

- **H:** With a caller-owned X11RuntimeSession over the three-app fixture, current runtime admission independently rejects an expired observation sequence and a stale binding revision before any backend emission.
- **T:** One distinct local Docker Desktop linux/amd64 X11 session; launch app-owned Inkscape, Calc and Chromium windows; route three observations and three dispatch programs through one runtime session/backend object. First hold binding current and stale observation sequence; next hold observation current and stale binding revision; final use current sequence/revision for harmless ESC + release_all. Preserve raw output and PNGs; run a separate read-only, network-disabled raw audit.
- **D:** Both negative controls must return their respective STALE_OBSERVATION and STALE_BINDING errors with zero backend emissions. All observations must be no-authority/no-input; the current neutral program must complete; per-program and final release must verify empty keys/buttons; independent audit and five main runtime Git blob comparisons must pass.
- **C:** Same pinned local derived image public-mcp-three-app-2907:formal01, image sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09; base image sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3; --pull=never --network none --pids-limit 512 --memory 4g --cpus 4. Runtime source read-only; evidence mount only writable. No workflow, model, remote service or Ollama interaction.
- **U:** Caller-owned runtime session only. A caller-supplied binding revision is an admission input, not proof that focus/modal/window replacement identity was refreshed correctly. Does not compose through public MCP's private session, run all four frozen perturbations through typed controller review, independently score app task effects, establish #2789 acceptance, performance or product readiness.

## Construction05 outcome

Three observations returned, each with no input and no side-effect authority. Negative admissions:

| Case | Current seq | Program seq | Current binding | Program binding | Result | Backend emissions |
|---|---:|---:|---:|---:|---|---:|
| stale observation | 3 | 1 | 1 | 1 | STALE_OBSERVATION | 0 |
| stale binding | 3 | 3 | 2 | 1 | STALE_BINDING | 0 |

The current seq/revision ESC + release_all program completed. Its own release receipt and final backend release both verified empty keys/buttons. Model/network calls 0/0; authority_granted=false.

- Runner SHA-256: e8005472ab14aaa406de67c52c4421fe9d725097162446759c7f15d83ef25b86
- Raw lineage SHA-256: 1f8d691f258658589a4afe590b2b21bdf4d431dc2b31ff78e72ffd41ca121f89
- Independent audit SHA-256: 976d6cc24bce8e0e9b1854ed156cd314392e9ac3174b786a47b41fa68c0564eb
- Audit: PASS_RAW_AUDIT, errors=[]; all five pinned runtime source Git blobs match.
- Local Docker AST parse for runner/auditor: PASS.

This remains construction evidence, not an allocation or the full #2907 PASS. Construction04 and all earlier STOP/control outcomes remain unchanged.

