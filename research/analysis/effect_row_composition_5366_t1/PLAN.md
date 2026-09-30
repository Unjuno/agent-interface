# Compositional effect-row contract T1

Allocation: `effect-row-composition-5366-t1-20260930-01`
Issue: [#5366](https://github.com/Unjuno/agent-interface/issues/5366)
Registration main: `6b1ad36c0628098c2d1c28b0a1b371db099aecce`
Frozen source main: `8265c1a19cbba7ab0f5316f27bdb59509269399d`
Branch: `research/effect-row-composition-5366-t1-20260930`
Path: `research/analysis/effect_row_composition_5366_t1/`

## H/T/D/C/U

**H.** Compositional rows propagate wrapper-polymorphic, nested, and branch effects before dispatch; native/remote unknown remains `EFFECT_UNKNOWN`. Conservative branch union may false-reject an actually safe chosen branch; count it explicitly.

**T.** Nine finite manifests: pure, direct read, polymorphic network instantiation, nested write masked by a wrapper, branch union whose observed branch is read-only, native unknown, remote unknown, valid transitive read+observe, and effect-row containment.

**D.** PASS_SCOPED iff no undeclared effect is admitted; unknown never becomes pure; valid transitive rows are admitted; false rejection is separately identified; all nine cases match the literal independent oracle; no dispatch, authority, or effect occurs.

**C.** Host-only deterministic Python 3.14.5 / Darwin arm64 / stdlib. No Docker/OrbStack CLI under current #5085 coordinator hold. Formal raw runner and raw-only audit once each, no retries.

**U.** Finite manifest arithmetic only; not proof of summary completeness, compiler soundness, non-interference, native/remote safety, or runtime benefit.
