# Issue #3573: portable MCP zipapp in OrbStack

## H/T/D/C/U

**H:** A deterministic zipapp built from frozen main can launch optional stdio MCP in an isolated OrbStack Linux/arm64 container, expose exactly two public tools, return observation PNG as a separate image block, dispatch one bounded save to an owned Tk fixture, persist one matching request/report, and verify input release.

**T:** Build from committed HEAD `79bd0410e7baac734be2190a9ae7200f91b5c940`; use an OrbStack image derived from the existing pinned Ubuntu 24.04/Python 3.12/MCP 1.30.0/X11 toolchain plus python3-tk. Runtime: `--network none`, read-only root, read-only source/archive, fresh writable evidence mount, private Xvfb and one owned fixture. In a temporary cwd and minimal environment, perform one MCP initialize/discovery, one read-only observation, and one dispatch typing a unique marker then Ctrl+S. No model/provider, retries, replay, host desktop, or external data. An independent auditor checks tool/call counts, image block and PNG, retained reports, exact fixture effect, release verification, teardown, hashes and manifest.

**D:** PASS only if every preregistered gate passes. Image build/preflight failure is STOP; absent MCP/tools is STOP; wrong effect/image/release is FAIL; incomplete lineage is HOLD. Never infer host registration, model-visible feedback, generality, or performance.

**C:** Frozen source/archive, pinned SDK and image lineage, private display, disposable fixture and unique marker. Runtime network disabled. Read-only observation precedes a single dispatch; fixture-side effect JSON is independent of tool response.

**U:** Whether packaged MCP remains functional under these actual container conditions.
