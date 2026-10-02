# WSL caller-selected feedback comparison Implementation Plan

> For agentic workers: execute natively with superpowers:executing-plans. The user explicitly prohibits subagents and authorizes continued integration; no separate plan approval is required.

**Goal:** Decide whether an existing caller-selected post-release wait reduces explicit observation roundtrips while preserving correct primary interpretation and saved effects.

**Architecture:** Use the existing public persistent Python API and MCPSessionOwner.inspect_after_dispatch(report, target, screen_region, capture_directory, wait_ms). No production API or default changes. A fresh bounded WSL study preserves the prior Docker/OrbStack #3700 study and the 18-phase comparison unchanged.

**Tech Stack:** Ubuntu24.04, WSL3.0.1 package / execution version2, Xvfb1280x800x24, Openbox, Calc24.2, primary model through functions tools, reused Python environment.

**Spec:** GitHub issues #3700 and #5256, plus the active thread goal. Source base: eacb1346866f660d9d34eb36cd9691fd8184e5ff.

## Global Constraints

One owned GUI allocation at a time; no Docker startup, sensors, helper models, background watchers, input replay or automatic target selection. Freeze executable/archive/plan/schedule hashes before GUI allocation. Main may advance; use the pinned source throughout. No production default change from these four cases.

Wait means fixed delay only: update_observed remains null. Post-input inspection is conditional on completed input and verified neutral releases. Inspection failure preserves the input result and forbids replay. Existing explicit one-use modal review/revision rules remain in force.

## Review Focus

- Metadata/image disagreement must withhold the image, preserve input effects and not permit replay.
- Partial/black primary presentation with unequal or unavailable pixels requires STOP, not coordinates inferred from another owner.
- Intermediate feedback requires one explicit read-only observation, not repeated capture until favourable.
- Expired/replaced modal review refuses; retain failure, never silently renew it.
- Host timestamps and primary declarations are distinct; missing ingestion/billing/provider snapshot cannot be filled with SDK latency or zero cost.

## Task1: Pin the existing implementation and prospective allocation

Files: this plan; runtime/results/wsl-feedback-successor-01/PLAN.md, schedule.json, owner.py, command.py, runtime.pyz, MANIFEST.json, FROZEN.json.
Consumes: public MCPSessionOwner, observe_in_session, dispatch_in_session, present_result, delivered-image association helper from immutable prior comparison commit.
Produces: four sequential fresh owners with seeds1002301..1002304 and fixed waits50/250/250/50ms; paired tasks A1/A2=431/683 for rows1/2,257/941 for rows3/4. Values are prospective, development-known, not held-out model tasks. Existing 20ms text pacing and100ms inter-cell input wait remain identical. Only post-release inspection wait differs and applies to all three input programs.

- [ ] Retain normal and -O existing test_mcp_session results; verify opt-in, retained lookup, inspection failure, release failure, target disagreement and wait argument checks. These inert tests are admission, not GUI effectiveness evidence.
- [ ] Create a distinct runner from the retained owner, removing compiled/changed-context/local conditional methods. Use original public dispatch/observe/explicit review only. Inject the frozen row values and wait; require exact allocation identity before creating a display.
- [ ] Build one portable archive from the pinned commit; retain source hashes and doctor/import checks. Compare all executable bytes with source manifest. Freeze plan, schedule and runner hashes in a committed FROZEN.json before the first session.

## Task2: Primary self-use without action replay

Files: the same bundle, per-row original commands/replies/PNG artifacts, primary-decisions.jsonl, cleanup/evaluation results.
Consumes: the frozen row and actual initial original PNG. Produces: original input effects and retained primary declarations.

- [ ] For each row, observe and ground fresh blank sheet from the actual image. Dispatch one batched two-cell entry, inspect its returned image, then Save only after expected visible values are established. No online saved-file/UNO/DOM oracle or OCR policy change.
- [ ] If the entry image cannot establish values, allow exactly one explicit observe. If still unknown, stop and score terminal failure. For format modal, review its original evidence explicitly before a separate confirmation program. If final feedback remains intermediate, allow exactly one explicit observation after confirmation. No other favourable recapture.
- [ ] Record a primary declaration before each next input and before close: source image hash, visible values/state, confirmed/intermediate/unknown and next decision. These declarations are authored by the primary, not automatic semantic validators. Timestamp receipt is a proxy, not model ingestion time.
- [ ] Limit each owner to10 commands,3 consequential input programs,900s lifetime and zero retries. Wrong/collateral effects, release failure, infrastructure/OOM or unavailable grounding halt the block; preserve remaining rows as censored. Wait the original live process handle rather than restart on tool timeout.
- [ ] Close the original owner, wait every owned child terminal, independently inspect the unique saved XLSX's entire nonempty cell set. Retain cleanup/release failures, wrong/empty files and unavailable results.

## Task3: Account and publish the integration decision

Files: report.json, README.md, source records and usage projection in the same bundle.
Consumes: all four rows plus setup and failures. Produces: a bounded integration decision, not a generic latency claim.

- [ ] Associate explicit tool call/output/primary-declaration boundaries and actual primary usage using the existing projection collector; preserve cache subsets and disjoint windows, preparation separately, actual PNG blocks, output and unknown billing. Same alias/configuration is observable; exact provider build and context equivalence remain unknown unless established.
- [ ] Report correctness, additional observations, input/observation roundtrips, actual fixed waits, host issuance-to-result-read intervals and primary-declaration source UTC intervals separately. Primary source declaration timing cannot prove exact first useful ingestion or human speed. A saved correct file alone cannot prove correct online interpretation.
- [ ] Retain HOLD unless correctness and observable feedback benefit survive both pairs without false completion, then require a distinct prospective held-out case before any caller recipe promotion. Four cases and changing conversation/cache remain exploratory. A regression yields REJECT; missing measurement yields HOLD, not invented benefit.
- [ ] Publish owned files once, normal PR/merge with expected head and fetched-main blob checks; update #3700/#5256/#57 with the actual result. Keep frozen old studies unchanged.
