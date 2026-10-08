# Issue #7934 decision-value acquisition — T0 A01

## Disposition

**FAIL_AUDIT; preserve as failed first outcome.** The WSLc simulator completed
and the independent auditor processed all 384 frozen observations, but returned
exit 1 because its preregistered expected-choice matrix incorrectly expected
`entropy -> xcheck` in the correlated profile. The frozen information baseline
maximizes information about the complete hidden state `(X,Y)`; `ycheck` reveals
Y perfectly (1 bit), while `xcheck` reveals less (about 0.278 bits). The raw
choice `entropy -> ycheck` is therefore consistent with the frozen rule. Do not
edit this audit or retry A01. Any follow-up must be a separately frozen
successor allocation.

## H / T / D / C / U

**H.** Decision-value acquisition should reduce realized route regret on
disagreement cases where low-cost/high-information observations do not change
the best safe route, while retaining the same choice on the agreement control
and never violating pre-admitted route gates.

**T.** Three finite profiles, 128 paired deterministic SHA256-derived seeds
each; compare cost-only, maximum-information, one-step decision-value, and exact
oracle choices. The full protocol and profiles are frozen in `protocol.md` and
`profiles.json`; source identities are in `FROZEN.json` and Issue #7934 comment
5987386681.

**D.** Formal disposition remains FAIL_AUDIT: the independent checker found one
expected-choice assertion error (`profile_choice_matrix`), with no other
independent errors. Its raw reconstruction verified 384 observations and all
per-policy decisions, route choices, costs, regret, and hard-gate counts. In
the disagreement profile, mean realized regret was 0.4765625 for both
cost-only and entropy, versus 0.25 for decision-value/oracle (improvement
0.2265625, above the frozen 0.05 threshold). In the agreement profile all
policies selected `xcheck`; decision-value and oracle both had regret 0.203125
and mean check cost 0.001. In the correlated profile, cost/entropy selected
`ycheck` (regret 0.25), while decision-value/oracle selected `xcheck` (regret
0.21875). All policy hard-gate violations were zero. Stale source, unknown
dependency, and 0.10 unmodeled-state-mass controls returned UNKNOWN with zero
checks; the one-route-denied control selected only route A with no check.

**C.** These synthetic results depend on the frozen route utilities, priors,
check likelihoods, costs, and 128 deterministic seeds. The oracle and
decision-value policy use the same correctly specified one-step model, so this
does not demonstrate advantage over an oracle or calibrated field beliefs.
The auditor defect prevents a formal PASS despite the raw/candidate agreement
on all other gates.

**U.** Method/audit result on a constructed finite state space only. No live
GUI, model, action, task effect, user-value, runtime safety, or latency result.
CPU-only was appropriate; no GPU experiment was performed.

## Runtime and retained evidence

One WSLc 3.0.1.0 container launch used Python 3.12.15 from
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`,
`--network none`, configured one CPU, read-only source, and writable output.
The CPU quota was configured but not independently measured. Simulator and
auditor each ran once; retries were zero. Exact raw observations, candidate
summary, both child stdout/stderr files, independent audit, and terminal status
are retained under `formal/`. The large raw/candidate JSON files also have
gzip transport copies and a byte-exact reconstruction manifest. `SHA256SUMS`
binds the complete local package except itself.

To inspect the terminal failure without rerunning the allocation, read
`formal/terminal.json` and `formal/independent_audit.json`.
