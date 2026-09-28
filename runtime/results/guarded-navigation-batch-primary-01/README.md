# Primary use: bounded navigation batching with incomplete immediate feedback

**Decision: HOLD as a default navigation recipe.** Six tasks succeeded, but four
of five navigation replies did not yet show the destination form. Read-only
recovery consumed most of the intended call reduction. Preserve the candidate
and its failures for testing under different explicit observation conditions;
this is not a rejection of bounded action batching in general.

The plan was saved before allocation. Source main 716d25286ec37999d8098cd63bf1731fae0d88d6,
portable runtime SHA-256 5c1fe40d133a9f59a1e0367dafe8a4091347d797532cab8c329c87983a49d030.
Fresh seed 991337, Linux/X11 :147, Chromium target 6291459, port 46735.
The primary assistant selected every action through the public MCP relay, with
unchanged complete text/image callbacks. No helper model, automatic target
selection, action queue, sensor or semantic polling was used.

Each navigation used one explicit guarded keyboard tail:
CTRL+L, wait 100 ms, type the known task URL, Enter, wait 100 ms.
The prior seed 991336 run split URL entry and Enter into separate model turns
and also waited 100 ms after typing. This candidate therefore changes both the
decision boundary and that intermediate delay. It is not an isolated latency
ablation; model context, seed, allocation and scheduling also differ.

| Navigation | Immediate reply | Explicit recovery |
|---|---|---|
| task 2, call 5 | Correct URL/tab and empty form; fading autocomplete remained | None |
| task 3, call 8 | SAVED body with address autocomplete | Read-only observe 9 confirmed destination |
| task 4, call 12 | SAVED body with address autocomplete | Read-only observe 13 confirmed layout B |
| task 5, call 18 | New URL but old SAVED body/loading indicator | Read-only observe 19 confirmed destination |
| task 6, call 22 | SAVED body with address autocomplete | Read-only observe 23 confirmed destination |

No navigation was replayed. All five destination reviews preceded form input.
All six exact entered values were visually reviewed before separate Save calls.
The predeclared stale-layout control (14) refused MISSING before input; batch
registration (15) explicitly grounded two new references from its image.
The independent oracle and submission history confirm six correct values once
each, with no missing, unexpected or duplicate submissions.

The plan expected 24 calls; actual use required 28: five observations (four extra),
two reference batches, 17 completed inputs, one refused input, two retained reads,
and close. The earlier seed 991336 run used 29 calls. The nominal five-call
reduction was offset by four additional observations; this is a descriptive
count comparison, not matched performance or token evidence.

The host span from first send to last reply was 217,600.0314 ms; summed send-to-reply
intervals were 9,164.4469 ms. The span includes historical reads and close, and is
not time to semantic completion. No isolated model timing, useful-feedback latency,
actual token/cost measurement or human-tempo conclusion follows.

Full final metadata was retrieved at 26; close 27 verified empty held keys/buttons;
read 28 returned the identical historical image/source 82 after close. Transport
and fixture exited 0. Tracked GUI child exits were 0/0/1, not all-success exits.

The 463-file archive retains the allocation, original plan, fixture source,
portable build, all requests/replies/images, ordered reviews, independent scoring,
cleanup and host timing. `python3 -O runtime/results/guarded-navigation-batch-primary-01/verify.py`
checks hashes, raw report/image parity, exact-once submissions, frozen navigation
tails, review ordering, explicit recovery, release and read-after-close without
extracting the archive or executing its code. Runtime implementation is unchanged.
