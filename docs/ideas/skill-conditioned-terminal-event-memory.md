# Skill-conditioned terminal-event memory for aliased GUI progress

Issue #8886 proposes a bounded evaluation of whether sparse, provenance-bound terminal-event retrieval helps distinguish GUI task progress when different histories produce the same current screen. It reports no implementation, model result, GUI correctness result, or broad memory claim.

## Skill-conditioned retrieval — #8886

- **Status:** open, unverified robotics-to-GUI transfer proposal; no experiment or evidence PR is recorded.
- **Source:** [Issue #8886](https://github.com/Unjuno/agent-interface/issues/8886); generic provenance-linked event-memory comparison [#7161](https://github.com/Unjuno/agent-interface/issues/7161).
- **Idea:** Under a fixed context budget, retrieve at most K prior terminal events relevant to the currently declared subtask. Records remain source-bound and distinguish observed effect, prediction, dispatch, reversion, stale generation, and `UNKNOWN`; retrieved memory cannot establish current freshness, target identity, lease, or action authority.
- **Proposed comparison:** `CURRENT_ONLY`, chronological raw history, generic latest-K event memory, and skill-conditioned terminal-event memory on visually aliased histories, alongside controls where the current screen suffices. Include not-run, verified-effect, reverted-effect, dispatched-but-unknown, and stale/mismatched-generation cases. A separate oracle establishes task state and exact effect; retrieval must not see oracle state.
- **Decision boundary:** A method pass would establish only discrimination and provenance on a frozen finite state machine. A later transfer claim would require a separate model-facing test with matched context budgets, fixed model/configuration, independent effect scoring, no increase in false completion or wrong-step action, and non-inferior current-state controls. The Issue does not authorize live application work or any runtime/default change.

## Related work and limits

#7161 owns the generic event-memory contract; #689 concerns feedback through an interaction; #5368 models action-conditioned hidden-state hypotheses; #28/#746/#751 address observation history or skill retrieval. The proposed distinction is selecting prior terminal evidence for the active subtask under fixed context cost, not treating memory as a substitute for current observation or effect verification. If #7161 or #689 owners take up the same comparison, consolidate rather than duplicate implementation ownership.
