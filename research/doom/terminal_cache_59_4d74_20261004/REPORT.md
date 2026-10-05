# Neutral engine terminal observability

Prospective issue record: #59 comment5977706258. One independent CPU construction, not the shared live game-control allocation. H/T/D/C/U frozen before one invocation.

The exact current-main V15 coherent-progress helper samples initial tic2/nonterminal and after a2.000669271s passive wait again tic2/nonterminal. One advance_action(1,True) update acknowledgment returns; subsequent tic74 sample reports finished/alive/no map exit under the declared35-tic timeout. Kill/death0 throughout. PASS_TERMINAL_VISIBLE_ONLY_AFTER_UPDATE_SCOPED/exit0. Explicit helper timeout_seconds1 is construction-only; the session main minimum10s guard was not launched or bypassed. Available buttons empty, positive inputcalls0, no model/X11controller/nativeinput. Engine close returns and is_runningfalse.

This demonstrates a terminal-state update dependence in this exact real ViZDoom1.3.0 ASYNC_PLAYER/FreedoomMAP01 condition. It does NOT independently identify engine timeout onset, allfieldatomicity/freshness, useful-gamefeedback, physicalrelease, closed-loop effectiveness or a neutral safe live update cadence. Receipt timestamp changes and equal tics alone cannot qualify freshness. advance_action may affect live execution; no runtime source adoption is proposed.

Full source/probe, argv/hashfreeze, raw stdout/stderr/RESULT/exit and generated engine artifacts retained. Fixed WAD is external; FREEZE pins its SHA and historical mount path; cached image/build dependencies remain external. Requested1CPU/512MiB enforcementunproven; kernelcgroup/swapwarning retained. No old formal/native allocation replay, no prior FAIL/STOP rewrite or GPU use. Independent archived-evidence review required before main publication.
