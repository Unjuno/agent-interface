# Issue #2447 stale-handoff probe — HOLD

Construction-only allocation `issue2447-stale-guard-construction-2447007`, Docker Desktop Linux/amd64, image `agent-interface-map01-lab:2447-preflight-20260927` (`sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`), network disabled, read-only root/source. One episode, zero retries, zero formal rows.

## H/T/D/C/U

- **H:** A stale observation must fail closed before authorizing the next subgoal.
- **T:** Seed 2447007, MAP01 drop setup, temporal gate, requested heading 120 degrees; stale TTL 250ms, injected wait 350ms; after the phase attempt, one bounded Right 190ms action and then a fresh screenshot/binding for the stale probe.
- **D:** PASS requires independently recomputed phase completion, prior bounded action with paired visual evidence and empty verified release, image/hash/binding integrity, observed age >TTL, typed stale refusal, and zero third-subgoal emissions.
- **C:** Single construction episode, same inherited detector/InputOwner path, Docker Desktop.
- **U:** Does not test other faults, comparative gates, formal rates, held-out transfer, cumulative completion, or acceptance of #2447.

## Result: HOLD_CONSTRUCTION

Stale subguard itself refused correctly: capture-to-decision age 459.293273ms >250ms; screenshot hash and focus/surface/geometry matched; `REFUSE_STALE`; next subgoal not issued; emissions=0. The preceding Right action had paired image flow (204 tracks; median dx -84.1493px) and verified empty release.

However the inherited phase detector reported `NO_DROP` (independent raw recomputation: 1 eligible pair, 0 drop pairs), while the runner set `extra_forward_issued=true` and proceeded. This is a gate/runner transition contradiction. No success claim and no retry; preserve as a failed construction allocation. Formal rows=0.

## Reproduction/evidence

Local lossless package SHA-256: `6d43673ce38adb86e6e82af3a0c279cb06751e1d8ac93f14cc0da6f3896f6723` (1,831,486 bytes). It contains 49 source/evidence manifest entries; raw episode evidence totals 1,812,826 bytes across 38 files. Full local package retained under `.agent-interface-docker-validation/issue2447/multisubgoal-stale-guard-2447007/`.

Next experiment must first isolate/fix the gate/runner transition in a new allocation or use a runner that refuses to advance on NO_DROP/UNKNOWN. Do not reuse this seed or relabel this result.