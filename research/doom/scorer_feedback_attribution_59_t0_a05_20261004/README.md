# Scorer feedback attribution construction A05

## H / T / D / C / U

**H:** Under the frozen `independent-progress-event-v2` schema, nonempty unknown positive-useful event kinds must be rejected. The current producer defines exactly `KILL_COUNT_INCREASE` and `MAP_EXIT` as positive-useful events.

**T:** Compare immutable A04 to the A05 wrapper on both actual producer-generated positive kinds, one unknown nonempty string, one misspelling, and producer-generated negative kinds. Run the unchanged 15-test A04 suite and four A05 cases once in a network-disabled WSLc candidate container. Run a separate raw-only auditor container once.

**D:** `PASS_METHOD_SCOPED` only if valid positive kinds retain A04's `SINGLE_POSSIBLE_INTENT_ENVELOPE` (with null intent and no causal claim), unknown/misspelled positives fail closed, producer negatives remain excluded, the unchanged A04 suite passes, and independent raw audit passes. No retry.

**C:** Forward compatibility may favor accepting new names, but frozen v2 producers must require an explicit schema/contract update. Even a closed vocabulary does not validate scorer truth or attribution.

**U:** Synthetic schema-construction only. No game/model/GUI/input/live trace, scorer accuracy, causality, useful feedback efficacy, recovery, survival, or MAP01 outcome is established.

## Frozen provenance

- Main: `af6d0f9842a2377fba736d2d65643b02690f99d9`
- A04 PR head: `8ddf0925539d03733d803b469586fb74a5b444e0`
- Candidate image ID: `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364` (`python:3.12-slim`, amd64, Python 3.12.15)
- Network: none; CPU 1; memory request 128 MiB; uid 65534; source bind read-only; no packages installed.

## Outcome

See [RESULT.json](RESULT.json), [AUDIT.json](AUDIT.json), and [COMMANDS.md](COMMANDS.md). A05 is PASS_METHOD_SCOPED: A04 accepted unknown well-formed positive event names while A05 rejected them; the current v2 producer's two positive kinds and negative-event exclusion passed. This is construction evidence only, with no live/game efficacy claim.
