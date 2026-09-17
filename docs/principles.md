# Thesis and Component Principles

## Core thesis

> **AI agents are smart. Their computer tools are primitive.**

Agent Interface starts from a falsifiable systems hypothesis:

> **For sufficiently capable agents, a growing part of computer-use cost comes from the interface rather than the model. If we improve the interface while holding the model, task, environment, and correctness requirement fixed, agents should be able to use computers with fewer model boundaries, fewer redundant observations, less serialization, lower latency, and less recovery work.**

This is a research hypothesis, not a claim that model capability no longer matters. The project should be judged by controlled comparisons where the model is held constant and only the agent-computer interface changes.

A useful test therefore looks like:

```text
same model
same task
same environment
same correctness requirement

only the interface changes
```

Then measure model calls, serialization, image/observation cost, latency, retries, recovery, and task correctness separately.

## Governing intent principle — preserve rich-model intent, localize refinement

> **Preserve rich-model intent; localize the high-frequency refinement loop.**

The frontier/rich model remains the source of semantic intent, strategy, novelty, and recovery. Agent Interface should make that intent **continue to produce useful, current-state-aware work while the rich model is reasoning**, by compiling or caching bounded execution structures that can observe, act, verify, and adjust locally.

The desired split is:

```text
rich model
    semantic intent / strategy / acceptable futures / stop conditions
            |
            v
Agent Interface
    compile or bind that intent into bounded local execution
            |
            v
local refinement loop
    observe -> act -> verify -> adjust
            |
            +-- still inside intent/envelope -> continue
            +-- stale / ambiguous / semantic change -> YIELD
```

Local execution may refine **how** an already-declared intent is carried out at computer timescales. It must not silently redefine **what** the agent is trying to accomplish.

This means:

- direct rich-model computer operation remains a first-class path; local execution is an optimization/delegation path, not a mandatory intermediary;
- deterministic macro, servo, watcher, cache, or graph should be preferred when it completely covers the local problem;
- a lightweight learned policy or supervisor is justified only for a real residual decision that simpler mechanisms do not close;
- a local policy may select only inside the current rich-model-authored intent/policy envelope and ordinary authority boundaries;
- prediction, historical evidence, cached decisions, confidence, and speculative branches never become current input authority merely by reuse;
- current evidence must be able to invalidate local continuation quickly; uncertainty or semantic novelty yields upward to the rich model;
- optimization should remove repeated semantic re-decision and waiting, not replace a stronger model's semantic competence with a weaker mandatory agent.

**Worker invariant:** every new mechanism or experiment should state (1) which rich-model intent it preserves, (2) what repeated/local work it removes from the rich-model critical path, (3) what current evidence invalidates or yields the local path, and (4) whether direct rich-model operation is the relevant baseline. A component-level PASS does not establish that the integrated architecture is better.

## Component principles

These principles constrain the eventual user-facing component, not only the current Python research harness.

### 1. Install quickly

A useful agent tool should be easy to obtain and start.

The target is a small number of obvious steps: install or unpack, start the local component, connect an agent, and use it. Basic computer control should not require app-specific integration work.

**Design consequence:** minimize mandatory dependencies, privileged setup, per-application configuration, and manual calibration before first use.

### 2. Work with every agent

The core should be **agent-agnostic and model-agnostic**.

OpenAI, Anthropic, open-source planners, local agents, remote agents, and future agent systems should be able to use the same computer-control component through a small stable boundary. Model-specific adapters may exist outside the core, but model-specific semantics should not define the core runtime.

**Design consequence:** keep the runtime vendor-neutral and expose a simple local protocol/library surface rather than coupling the control layer to one model API.

### 3. Do not stop the agent's thinking

When an agent acts, feedback should arrive as soon as useful evidence exists.

The control layer should not make the agent wait for a full screenshot, a fixed sleep, a long timeout, or a complete local workflow when a smaller trustworthy signal is already available. The goal is to minimize **agent idle time**: time during which the model could continue reasoning but is blocked waiting for the computer interface.

Prefer:

```text
action
  -> immediate local acknowledgement / event
  -> incremental state-change feedback
  -> compact verification result when possible
  -> richer visual observation only if uncertainty remains
```

over:

```text
action
  -> fixed wait
  -> full screenshot
  -> only then return control to the agent
```

**Design consequence:** event-driven feedback, streaming semantic events, latest-only visual state, local verification, and early-return APIs are preferred over blocking polling loops.

This principle does not mean returning unverified guesses. Fast feedback must remain truthful about its confidence and completeness. If a semantic effect is not yet known, return the strongest known local state and continue monitoring rather than pretending completion.

A key benchmark metric should therefore be **action-to-first-useful-feedback latency**, not only total task wall time.

### 4. React at local computer timescales

Deterministic control mechanics should execute locally whenever they do not require semantic reasoning.

Input delivery, event detection, state-change tracking, retry, local verification, and fine motor correction should not cross a remote/model boundary merely because the architecture makes that convenient.

**Design consequence:** keep high-frequency loops in-process or in low-overhead local IPC. HTTP/MCP-style boundaries belong outside the motor loop.

No universal millisecond target is claimed yet; the research should measure achievable latency per backend and workload before freezing one.

### 5. Universal before optimized

An unknown application must work before it has been learned.

Application-specific methods and workflow caches are optimizations over universal keyboard, pointer, focus, text, observation, and reactive control. They must not become prerequisites for basic correctness.

**Design consequence:** every optimized path needs a generic fallback.

### 6. Preserve information, remove waste

Optimization should remove repeated work, not hide information the agent still needs.

Examples:

- unchanged screen -> do not resend it;
- irrelevant changed region -> suppress it;
- deterministic postcondition -> verify locally;
- stale optimized route -> deopt before executing it;
- repeated successful trace -> reuse a semantic method;
- uncertain state -> escalate to richer observation.

This is the central test for token and latency optimizations: **what work disappears, and what information remains available?**

### 7. Correctness is the hard gate

A faster interface that silently loses task-relevant state is not an improvement.

Every optimization should preserve a fallback path and be promoted only after fresh/hidden evaluation under the same task and environment constraints.

## Practical acceptance criteria

A future user-facing Agent Interface component should aim to satisfy all of the following:

- easy to install and start;
- usable by multiple agent/model stacks;
- useful on an unknown application before learning app-specific methods;
- immediate or incremental feedback after actions;
- no unnecessary model round trip in deterministic local loops;
- explicit uncertainty instead of fabricated completion;
- local recovery and fallback when an optimization becomes stale;
- measurable reductions in agent idle time, model boundaries, observation cost, and recovery work at equal correctness.
