# MAP01 hop-15 plateau diagnostic

Issue-level disposition: **PLATEAU_SCORER_AMBIGUOUS**.

The source-frozen analyzer's first output found an apparently perfect concentration: all 8 retained #652 runs first reached minimum structural hop 15 in sector 29, and its all-two-sided graph assigned the hop-14 neighbor sector 34 through linedefs 175 and 201. That automated output was `PLATEAU_COMMON_INTERACTION_SCOPED`.

The retained line/sector metadata in the same output invalidates treating that graph edge as an ordinary traversable progress edge. Sector 29 is floor/ceiling -64/64. Sector 34 is -32/16, so the candidate boundary has a +32 floor rise and only 48 units of vertical opening. All eight trajectories approach one of these boundaries to 16.006-16.022 units but none enters sector 34.

A construction-only hybrid graph that required static clearance for ordinary edges but admitted special edges did not repair the metric: only three exit-side sectors remained reachable and sector 29 became disconnected, because MAP01 contains dynamic door/lift interactions that are not represented by initial static sector heights.

A more useful retained fact is independent of the false hop label: all 8 trajectories enter sector 165 after sector 29, while 0/8 enter sector 35. The 165->35 boundary is linedef 198, special 90, tag 1, segment (1152,-320)->(1024,-320). This nominates a next *live ordinary-observation* interaction/subgoal experiment. Hidden sector identity must remain scorer-only.

Consequently the merged #666 numeric structural-hop output remains immutable evidence of what that scorer computed, but it must not be cited as validated playable distance-to-exit. The coverage result is still a coverage result; its relation to task progress remains unresolved.
