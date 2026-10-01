# Text route keymap freshness v1

Question: is a payload-aware route decision still safe if the keymap changes after route selection but before first input?

Finite formal schedule: three fresh private Xvfb cases in fixed order US→US, US→German and US→French, payload `@`. Under the initial US map compile a direct-key plan. Then apply the target map before input and compare: (1) intentionally unsafe execution of the stale compiled plan; (2) retained execution-time whole-payload preflight; (3) fresh payload-aware reselection under transparent and explicit clipboard-side-effect budgets, with clipboard actuation only when freshly selected.

Hard gates: unchanged-map control remains exact; German/French stale-plan negative controls produce a non-`@` effect; retained execution-time preflight refuses changed-map direct input before emission; fresh transparent reselection yields no route; fresh clipboard-authorized reselection chooses clipboard and produces exact `@` without preceding direct emissions; candidate target map remains invariant and physical input ends empty.

H: route selection is advisory, not an authority token. Environment change invalidates direct eligibility. D: PASS only if all three cases and all hard gates pass. C/U: private X11 Group1 level0/1 fixture mutation only; no full XKB/Office/Wayland/Windows/macOS/IME/token/product claim.
