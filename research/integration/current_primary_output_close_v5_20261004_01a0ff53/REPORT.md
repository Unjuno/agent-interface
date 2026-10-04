# Primary stdio output-close V5 addendum

The source candidate was created from main `9c3a6b8a761e460baa6a3c8c801c93a34f3b7252`. Main later advanced to `a5f2bf291787000627abbc12c123af4bd2873d5c`; the selected runtime, workflow, test, and test-dependency paths are unchanged between those commits. No main write occurred.

The repair observes a silent output `close` during each write, during line admission, and across the outer primary owner's startup and cleanup lifetime. It retains the first failure, blocks new dispatch after closure, waits for already accepted work, and never replays it. When Node flags already show stdout closed, it refuses before host startup. A closed receiver whose Node flags remain open is outside this guard's proof.

Local verification used macOS Node 26.7.0 and private inert fixtures:

- The 17-module workflow Node command passed **211/211** on macOS Node 26.7.0 (PID 85791) and independently **211/211** on macOS Node 22.23.3 (exit 0). The separate strict UTF-8 module passed **15/15** on Node 26.7.0. Exact argv, stdout, stderr and receipts are retained here and under `workflow-native-linux/node22-local/`.
- The focused whole-owner module passed **4/4**, PID 84302, exit 0. Its startup-close witness records `PRIMARY_OUTPUT_CLOSED`, no ready row, no exchange directory, all listeners retired, and fixture relay exit 0. The in-flight capacity check is deliberately released after output close; the relay fixture does start and is then closed. This result does not prove startup can be cancelled once asynchronous host initialization begins.
- `git diff --check`, Node syntax checks and workflow YAML parsing passed.

The hosted Native MCP v1 workflow passed on head `6faf147`: Node host tests, Python/native integration and strict UTF-8 steps succeeded; its retained Python 3.12.14 result reports 445 protocol and 205 harness tests passing on Ubuntu. The complete runner output and inert close witnesses are retained under `workflow-native-linux/run-37165227376/`. No GUI, physical input, model/provider, formal allocation, task-effect or input-release experiment was performed. Full computer-control correctness, finite recovery, latency and total-resource claims remain unproven.

The PR changes the primary stdio module, the workflow and two output-close test modules. Evidence and exact hashes are recorded in `MANIFEST.json`. PR #7326 is the fresh draft proposal; old PR #7248 was superseded and closed unmerged. Its review state and proposal digest do not transfer. Main sends and unknown sends remain zero.
