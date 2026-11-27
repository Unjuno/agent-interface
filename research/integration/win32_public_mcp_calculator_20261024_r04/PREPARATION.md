# R04 — corrected result binding and same-session effect capture

R03 retained a completed normal-path action and verified neutral release, but its harness searched `interface_results.target_generation` instead of `interface_results.action.target_generation`; it therefore omitted the planned same-session post-action observation. The only later public screenshot exceeded the frozen 90-second bound, so R03 remains strict `FAIL_OR_UNKNOWN`. R03 raw is unchanged.

R04 fixes that result binding and uses a unique attempt/program ID. It begins from the retained Calculator display `1042`, then clicks `C` followed by the fixed `314 + 728 =` program. It makes one pre-action physical-screen observation, one validation, one dispatch, at most five exact-call read-only result polls, and one same-session post-action observation only after completed action plus neutral release. The total bound is 90 seconds; no recovery or replay is allowed.

A read-only sky screenshot was saved before the public-MCP attempt as `pre-run-sky-observation.jpg` (SHA-256 `e845390dec2d6a76d54b2fec0489117d66879d0e103930be40e3bea892a04127`). It is setup context and is not counted as the trial’s single pre-action MCP observation. This is a user-authorized native Windows PC run; WSLc and Docker are not used.
