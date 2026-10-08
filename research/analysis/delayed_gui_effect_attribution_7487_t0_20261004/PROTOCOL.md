# Frozen T0 protocol and H/T/D/C/U

## H — research hypothesis (not tested by T0)

In a consented, non-consequential vignette study with identical event facts,
longer action-to-effect display delay may reduce correct event-to-source
attribution in a chronological summary; a source-bound per-effect receipt may
attenuate that loss without increasing false certainty for unknown provenance.
A null is plausible. T0 makes no inference about this human hypothesis.

## T — this rung

T0 has no participants. One finite synthetic ledger has five cases: an agent
link, a human/external link, a delayed unrelated external effect, overlapping
actions with a ledger-declared link, and genuinely unknown/conflicting source.
Cross each with 300 ms and 1500 ms display delay and two renderings, producing
20 records. Delay changes only `effect_display_at_ms`; summary and receipt share
all visible base event facts and ordering. The receipt adds only the frozen
ledger's declared source-link fields. No link is inferred from timestamps.

## D — decision rule

`PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 20
records from `frozen_ledger.json`, summary/receipt fact parity and delay parity
hold, all four receipt provenance fields match the ledger, the UNKNOWN case
remains UNKNOWN, and six effective actor/action/target/effect/order/link-status
mutations are rejected. Any mismatch is FAIL/HOLD, preserved without retry.
This gate tests construction and provenance mechanics, not the human H.

## C — alternatives and confounds

Users may rely on actor/action labels independently of delay; timeline order
may suffice; receipts may add useful explicit causal structure or may be
redundant. A human advantage could be caused by extra facts, so the T1 design
must keep all non-link facts and timing identical and vary only relationship
presentation. T0's mechanical fact-parity audit does not establish equal human
interpretability or eliminate salience effects.

## U — limits

Synthetic ledger provenance is stipulated, not discovered. No human, GUI,
application, model, actual delayed rendering, causal ground truth, confidence,
attribution, trust, blame, authorization, success, or safe-retry behavior is
measured. Participant T1 requires separate ethics/consent approval. Container
preflight stopped on an OrbStack daemon blob-read failure; host-only execution
is not isolation evidence.
