# Issue #5306 real-options boundary T1

Status: frozen deterministic host-CPU boundary experiment; no claim about deployed systems or the parent #5306 hypothesis.

## H / T / D / C / U

**H.** In a one-step binary action problem, correctly risk-weighted value of information already prices keeping an irreversible action unexercised. Adding a separate expected-downside “option premium” can therefore duplicate value and induce a dominated wait. This tests the real-options extension in Issue comment #5908987034, not the full sequential VOI hypothesis.

**T.** Exhaustively evaluate 405 hand-frozen combinations: safe-state probability {0.20, 0.40, 0.60, 0.80, 0.95}; total irreversible/downstream loss {1, 4, 16}; binary-test sensitivity {0.60, 0.80, 1.00}; false-pass probability {0, 0.10, 0.30}; and delay/deadline cost {0, 0.05, 0.20}. Compare (1) immediate expected-utility admit/yield, (2) one-step risk-aware VOI continue/stop, (3) exact one-step Bellman continue/stop oracle, and (4) the risk-aware VOI plus a separately added immediate expected-downside premium. No random sampling, learned policy, GUI, model, network, or external effect. Runner emits the complete 405-row raw table; a separate Decimal-based auditor independently reconstructs all rows and summary metrics.

For safe prior p, loss L, sensitivity s, false-pass f and delay cost c:
- immediate value = max(0, p − (1−p)L);
- value after the test = max(0, p·s − (1−p)L·f) + max(0, p·(1−s) − (1−p)L·(1−f));
- continue value = test value − c;
- one-step VOI = continue value − immediate value.
The deliberately additive premium arm adds (1−p)L only when immediate expected utility admits the action. This arm is a falsifiable “separate premium” operationalization, not a definition of all real-options methods.

**D.** PASS_REDUNDANCY_SCOPED only if all 405 unique cases audit; risk-aware VOI and the Bellman oracle agree on every stop/continue decision; the additive-premium arm causes at least one wait whose exact continuation value is below stopping value; and no case violates value arithmetic. Otherwise FAIL/STOP. This can reject a redundant one-step premium; it cannot reject multi-step real-options methods.

**C.** Synthetic, fully specified binary state; risk-neutral expected value; known test characteristics; one optional observation; delay cost is additive; no state transition while waiting. The “total loss” parameter is assumed calibrated.

**U.** No empirical transition calibration, multi-step belief updates, nonstationarity, adversarial behavior, correlated evidence, dynamic deadlines, live authority, or GUI/task safety. A broader sequential study and the main #5306 VOI comparison remain open.

## Provenance and execution gate

Base main: 6b1ad36c0628098c2d1c28b0a1b371db099aecce. Additive branch/path: research/voi-option-5306-t1-20260930 / research/analysis/voi_option_5306_t1/. Source files and exact branch head must be read back and pinned in the Issue before the one runner invocation. Docker/OrbStack is not used: #5085 currently forbids Docker CLI use without an exact owner/resource assignment, and C: has zero free bytes. This is a file-write-free local CPython boundary run, not a container/formal Docker allocation.