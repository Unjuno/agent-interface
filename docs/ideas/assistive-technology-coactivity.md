# Assistive-technology co-activity and non-interference

## Distinct questions in #5922 and #8880

### Presentation-configuration effects — #5922

#5922 asks whether an agent route preserves the intended task effect across accessibility presentation settings such as text size, zoom, contrast, or reflow. Its original T0 was invalidated: candidate stdout was missing, the auditor could not run, and a later candidate rerun was explicitly invalidated. Thus no valid audited result exists. The issue's later scope note says concurrent human/assistive-technology input is a distinct ownership interaction, not merely another visual setting. See [Issue #5922](https://github.com/Unjuno/agent-interface/issues/5922) and invalidation record [PR #5930](https://github.com/Unjuno/agent-interface/pull/5930).

### Concurrent human/AT and agent operation — #8880

**Status:** Open, unverified transfer and evaluation-method proposal. No current product defect, WCAG violation, or participant result is claimed.

#8880 asks whether a person can continue screen-reader, switch, or keyboard navigation while an agent operates without the agent unexpectedly moving focus/caret, consuming human input, obscuring a cue, or committing an action against a target that changed after observation. This is distinct from merely preserving the same final task effect across static presentation configurations. Relevant prior work includes #5922's presentation question, #5800's overlay interference question, and #6049's agent-facing live-region cues.

The issue proposes a staged test: first a disposable fixture with no human input, then a separately frozen simulated AT/human event interleaved between observation and action, plus a disjoint-surface control. Freeze focus/caret ownership, intended effect, allowed action, and an independent oracle. No real AT session or participant study is authorized by the proposal. See [Issue #8880](https://github.com/Unjuno/agent-interface/issues/8880).

## Evidence and scope boundary

WCAG and WAI-ARIA guidance provide relevant web-content and dialog-pattern requirements; they do not certify native backends or define a complete co-active agent/AT ownership protocol. These Issues establish neither accessibility conformance nor safety. Any future test should preserve explicit human/AT ownership and test focus, caret, and input routing as separate outcomes rather than infer non-interference from task completion alone.
