# Passive decision samples and independently observed partial effects

The previous shared Calc episode needed six model decisions and60.808s.
Inspecting its refused A2 patch finds100 changed pixels on four horizontal rows
of the25x25 patch, with identical X binding. The full-frame changes include the
formula/status area. The images are consistent with a UI update after entering
A1, but do not establish an internal cause such as caret blinking. The original
target-patch refusal remains unchanged. The post-confirmation images also differ.

## Candidate and live evidence

decision_pair_v1 collects at most three new passive observations before the next
model decision. It compares full pixels and coherent sampled focus/surface/input
context, checks increasing captures/sequences and a correlated recent clock, and
returns received_pair_equal or sample_limit with the latest image. Exhaustion
still delivers explicit uncertainty; equality is not semantic readiness, effect
verification, or input authority. No action is retried or continued by this helper.
The bound counts captures; it is not a hard wall-clock deadline and cannot
preempt a hung capture callback. The live caller retains its per-exchange limits.

sampled_decision_calc_v1 integrates it after each action/refusal. The original
action resolution is retained in planner feedback even though passive programs
advance the journal. Added captures, full comparisons and elapsed cost are
audited separately. The existing target gate and phased execution stay unchanged.

| Episode | Model calls | Capture to evaluation | Input tokens | Output tokens | Added sampling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prior shared-phased-calc-01 |6|60.808s|58,775|1,214|none|
| sampled-decision-calc-01 |4|45.850s|39,454|726|1.332s /4 captures|
| sampled-effect-calc-01 |3|32.378s|29,550|514|0.868s /3 captures|
| sampled-effect-calc-02 |4|45.181s|39,456|821|1.293s /4 captures|

All four saved480/192 correctly. These are single episodes, not a matched speed
experiment. In particular, the new runs combine both cell entries in the first
model proposal; the prior run split them. Cache usage, model choices and audit
instrumentation also differ. Fewer calls cannot be attributed to sampling. The
sampling candidate remains opt-in, and an extra Save persists in two new runs.

The decision collector controls cover an archived transition followed by a
synthetic equal sample, continuing alternation, held input, stale samples and an
invalid bound before capture. They are not proof of UI readiness. Live audits
reconstruct every added clock/observe/clock exchange and collector verdict,
model image/prompt/response, exact transported frames, journal and saved cells.

## Saved-effect diagnostic and retained failure

The first diagnostic, sampled_effect_calc_v1, tried to copy runtime/sheet.xlsx
mid-episode. That file is only exported during teardown, so all five intermediate
reads were unavailable. Its successful final task does not repair the missing
diagnostic evidence. Source, unavailable records and that run are retained.

sampled_effect_calc_v2 locates the workbook in the private Calc descendant's
arguments, restricted to the episode's /tmp/realapp-x-* directory. During the run
it copies raw bytes only; model prompts receive neither paths nor saved values.
The independent audit parses copies after the episode. This is fixture-specific
diagnostic instrumentation, not a general GUI observation channel. Copies have
time/order references but are not atomic with the screenshots.

The corrected run establishes this sequence:

- Before confirming the format dialog, saved A1/A2 are still empty.
- After confirmation, the program says needs_decision/focus_changed and zero
  completed steps, yet the copied workbook already contains480/192.
- After the additional passive pair, the same values remain persisted before
  the next model begins. That model nevertheless proposes another Save.
- The later Save changes worksheet XML bytes, while the required cell values
  remain480/192. Only those declared values establish the task effect here;
  arbitrary workbook equivalence and absence of collateral changes are unproven.

audit_persisted_effect_v1 reproduces this counterexample. Thus a released,
interrupted program can already have the required saved effect. This does not
mean interrupted programs should be reported as successful or replayed. It means
program status and application effect need distinct evidence-backed presentation.

## Decision and next comparison

Keep sampling opt-in. It supplies newer sampled images at measurable cost, but
does not by itself remove extra model decisions. The shared caller currently
uses status=refused for both a pre-input refusal and admitted interrupted input;
that conflation is a concrete presentation issue to address next. Preserve raw
terminals, partial progress, unresolved delivery and unknown semantic effects.
Evaluate any revised vocabulary on fixed observations/context before claiming
fewer retries, then use fresh live tasks.

This work informs [Issue34](https://github.com/Unjuno/agent-interface/issues/34),
[Issue39](https://github.com/Unjuno/agent-interface/issues/39) and
[Issue50](https://github.com/Unjuno/agent-interface/issues/50). It does not implement
their full effect contracts, negative-outcome vocabulary or semantic deltas.
Those issues remain open; no GitHub comments or status changes were made.

Evidence directories: decision-pair-controls-01, sampled-decision-calc-01,
sampled-effect-calc-01 and sampled-effect-calc-02 under results. Replay with the
corresponding audit_sampled_* scripts and audit_persisted_effect_v1 under Linux.
The main live-tempo and domain-coverage goal remains unfulfilled.
