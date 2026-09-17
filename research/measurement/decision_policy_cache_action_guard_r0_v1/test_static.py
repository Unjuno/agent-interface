from __future__ import annotations

from dataclasses import replace

from candidate import EFFECT, INACTIVE, YIELD, run_cached_action_guard, run_cached_supervisor_only, run_redecide_every_cycle
from oracle import exact_reference, guarded_cache_reference, regime_at
from scenario import ACTION_TIMES_MS, HARD, AMBIG, generate_scenarios


def test_generated_discriminators():
    for s in generate_scenarios(1000, 17):
        assert any(regime_at(s, t) == AMBIG for t in ACTION_TIMES_MS)
        assert any(regime_at(s, t) == HARD for t in ACTION_TIMES_MS)
        assert all(t % 20 != 0 for t in range(s.transient_hard_start_ms, s.transient_hard_end_ms))


def test_reference_matches_oracle():
    for s in generate_scenarios(1000, 19):
        got = [d.disposition for d in run_redecide_every_cycle(s)["decisions"]]
        assert got == exact_reference(s)


def test_guard_matches_oracle():
    for s in generate_scenarios(1000, 23):
        got = [d.disposition for d in run_cached_action_guard(s)["decisions"]]
        assert got == guarded_cache_reference(s)
        for t, d in zip(ACTION_TIMES_MS, got):
            if regime_at(s, t) in (HARD, AMBIG):
                assert d != EFFECT


def test_supervisor_only_has_discriminator():
    stale = 0
    ambiguous = 0
    for s in generate_scenarios(1000, 29):
        got = [d.disposition for d in run_cached_supervisor_only(s)["decisions"]]
        for t, d in zip(ACTION_TIMES_MS, got):
            if d == EFFECT and regime_at(s, t) == HARD:
                stale += 1
            if d == EFFECT and regime_at(s, t) == AMBIG:
                ambiguous += 1
    assert stale > 0
    assert ambiguous > 0


def test_generation_mismatch_fails_closed():
    s = next(generate_scenarios(1, 31))
    s = replace(s, current_generation=s.cache_generation + 1)
    got = [d.disposition for d in run_cached_action_guard(s)["decisions"]]
    assert got[0] == INACTIVE
    assert all(d == INACTIVE for d in got)


def main():
    tests = [
        test_generated_discriminators,
        test_reference_matches_oracle,
        test_guard_matches_oracle,
        test_supervisor_only_has_discriminator,
        test_generation_mismatch_fails_closed,
    ]
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)} static tests")


if __name__ == "__main__":
    main()
