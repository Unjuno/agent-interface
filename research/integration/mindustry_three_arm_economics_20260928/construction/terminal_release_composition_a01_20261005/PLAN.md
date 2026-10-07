# Terminal and release contract composition A01

Status: frozen before the in-memory matrix run. This is a host-only construction
test for the two complementary adapter changes proposed in PRs #7682 and #7683.

## H / T / D / C / U

**H.** When the terminal-completion guard and strict release-state guard are
combined, the socket adapter will issue a successful receipt only when both
conditions hold. Separate passing controls do not establish the conjunction.

**T.** Derive one candidate adapter from the exact `target_socket_submit_v1.py`
blob at PR #7683 head `1d7bb20bcde67333f58e41a24f8dce68f8561ffd`, then add the
two-line exact-status guard present at PR #7682 head
`bd0ba260acf885d7b859d665571b2c3260666642`. Exercise an 8-by-10 in-memory
matrix: eight terminal-status forms crossed with ten release-state forms. Keep
the action ID, command receipt, authority, response boundary, and cursor fixed.
Use a fresh submitter per cell; capture acceptance/rejection and receipt.
No socket, GUI, game, model/provider, Docker, or OS input is permitted.

**D.** Exactly the two `completed` × valid-release controls must return the
successful receipt. All other 78 cells must raise `SocketSubmitStop`. Any other
outcome is a composition failure; malformed evidence or source mismatch is
STOP, not a scientific failure.

**C.** This establishes a narrow protocol conjunction only. A synthetic response
can omit producer/runtime behaviors; status and release correctness do not
prove a physical key-up or application effect.

**U.** No live upstream producer, Mindustry session, physical release, target
admission, model usage, task success, formal allocation, or economics was
measured. The source branches are open PR candidates and are not main evidence.

## Frozen identities

- Current main at freeze: `c99d93a2c81945f0946173e48247bdd49e32a02a`.
- PR #7682 head: `bd0ba260acf885d7b859d665571b2c3260666642`.
- PR #7683 head: `1d7bb20bcde67333f58e41a24f8dce68f8561ffd`.
- Adapter path in both candidates: `research/integration/mindustry_three_arm_economics_20260928/target_socket_submit_v1.py`.

The builder verifies both commits are available in Git, derives the exact
combined source, and records its SHA-256. `audit.py` independently reconstructs
that candidate from the pinned Git objects and audits every expected cell.

## Frozen matrix

Statuses: `completed`, `failed`, `cancelled`, `needs_decision`, explicit null,
missing, boolean true, and uppercase `COMPLETED`.

Release variants: minimal explicit-empty control; source-shaped owner-release
control; held key; held button; missing keys array; missing buttons array;
unverified; missing release; unknown extra field; and malformed producer
metadata.

The two valid release variants pass only with exact status `completed`. This
matrix does not change either PR's source or the #5130 formal allocation.
