# Successor experiment preregistration — Issue #3628

## H/T/D/C/U

- **H:** A passive per-widget Tk bindtag inserted immediately before the `Entry` class bindtag records the actual public-MCP `Control_L` then `s` keypress exactly once, returns `None`, and leaves the existing save handler/effect and explicit post-action observation intact.
- **T:** Following a passing construction and all seven preflight audit controls, perform exactly three sequential, fresh Linux/arm64 OrbStack allocations using the pinned portable MCP archive and one persistent stdio connection per allocation: initial `interface_observe`, one bounded `interface_dispatch` with a fresh marker and verified release, and one separate read-only post-action observe. Then perform exactly one independent raw-only audit over the three immutable rows. No retries or replacements.
- **D:** Scoped PASS only if all rows contain precisely one ordered passive `Control_L`,`s` pair for the save chord, exact independent effect marker, one dispatch, valid fresh post-observation/image, empty verified release, full hash closure and cleanup, and the frozen independent audit has zero failures; every specified negative control must be rejected. Any miss remains HOLD/FAIL/STOP without promotion.
- **C:** Same task, public MCP tools/order, chord, fixture state and save/effect behavior, image/platform, observation semantics, and runner as #3618. Only the additive passive audit bindtag and its event receipt differ. Existing #3587/#3618/#3620 evidence is excluded and unchanged.
- **U:** Fixture-level container evidence only. Does not test registered-host acknowledgement/model visibility, latency/cost, broad GUI reliability, or close #3370.

## Freeze

- Issue: #3628; base main: `e4fa787eba9dd527d1d29727d6e88e2508fba9cc`.
- Container: `issue-3573-portable-mcp-orbstack:20260920`, image ID `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`, `linux/arm64`, network none, read-only root/source/archive/runner, `/tmp` tmpfs.
- Portable archive SHA-256: `e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624` (unchanged from #3618).
- Runner SHA-256: `c4ba017b3685d6d4ba78cea2b8ccbecdae6d769e41712da4c1c87e1b88135f75` (unchanged from #3618).
- Raw-only audit SHA-256: `aabf29ee6e8d5f74af2f5a0bf3b31df0f840462fe0f97a09db7a4f4b24f5e997` (unchanged from #3618).
- Patched fixture SHA-256: `47ebb8ac9fb57cd318ffb3f0653aee9d3b10343d61b41bf2d6c9521f2af5e4ea`.
- Seven-control preflight audit SHA-256: `5d5282335a8e11fe85d7a005a4d912c7080f4d10555d96d3f07a3843a50a0a59`.
- Formal evidence paths: `evidence/formal-01`, `formal-02`, `formal-03`; one read-only audit output at `evidence/independent-audit`.

## Preflight result

One OrbStack construction allocation `formal-05b63c13820e` produced marker `orb3587-c764150e228f`. The passive tag recorded the ordered chord exactly once; the independent fixture effect equals the marker; calls were observe/dispatch/observe; Xvfb exited 0, fixture was reaped, and its X11 socket was removed. All seven frozen preflight controls passed. Raw construction artifacts are kept separately at `/private/tmp/3628-construction` until copied verbatim into the evidence package. This construction row is not a formal row and is excluded from the three formal allocations.

Freeze was recorded on Issue #3628 before the first formal allocation. The resulting frozen comment is retained in the issue history.
