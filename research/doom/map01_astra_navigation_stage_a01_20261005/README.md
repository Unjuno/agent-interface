# Astra MAP01 navigation-stage audit A01

## H / T / D / C / U

**H:** The 13 exact model-input frames show a sequence of distinct visible route stages—approach to a door, open-room view, lower channel/ledge, corner, and stair approach—but do not establish exact world position or completed navigation.

**T:** Manually label the 13 retained, hash-bound input frames with visible landmarks; join those labels to the corresponding primary commands and viewport-effect receipts in the retained report; verify the frozen terminal score and source hashes. No candidate, game, model, or input is rerun.

**D:** `PASS_SCOPED_VIEWPOINT_STAGES_HOLD_EXACT_ROUTE` requires all 13 frame hashes to match, the door-to-room and later channel/stair views to be present, the command/receipt totals to reconstruct, and the terminal score to remain `map_exit=false`, `player_dead=true`, one kill. Exact route progress remains HOLD because these are viewpoint images without position or route-node telemetry.

**C:** Camera rotation and translation can both change visible geometry. A visible-change receipt is a viewport effect, not a measured position change or objective completion.

**U:** Labels are manual and retrospective, from one failed trajectory. The evidence gives no player coordinates, exact route, enemy identity, or distance to the MAP01 exit. It does not establish why navigation failed or whether any local policy caused death.

## Observed stages

The retained frames depict a starting passage, a closed door, an open room with an enemy visible, a hazard-striped ledge/lower channel, a close corner, a raised barrier with stairs visible to the left, a close wall, and the terminal low-view frame. The action report contains 26 primary-command receipts: 25 say `visible_change` and one `no_visible_effect`. The scorer records one kill, no map exit, and death. These observations separate visible scene changes from the objective outcome; they do not establish an exact traversed route.

The independent audit binds each annotation to the original PNG and source report, event stream, video, environment and terminal score. The initial freeze uses the historical main SHA recorded by the retained Astra analysis. No current runtime source, player state, or live allocation is implied.
