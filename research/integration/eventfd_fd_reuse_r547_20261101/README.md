# Experimental eventfd descriptor reuse: r547

In one isolated Linux test run, the draft notifier's ordinary unreadable/readable
control passed. A closed descriptor correctly produced an error after changing
the prototype to reject unexpected poll flags. The third test intentionally
closed the eventfd, reused its integer with an empty pipe using `dup2`, and
required an error; no error was raised, so the regression failed (unittest exit
1). Under this injected ownership violation, poll readability alone cannot
identify the original eventfd. A separate earlier local probe with a readable
pipe likewise did not reject the replacement; that observation is not in this
run's raw archive.

The conditions list the ordinary control before the closed-fd case, but unittest
actually ran the closed-fd case first by name. Each case creates its own fd;
the differing order is nevertheless a recorded deviation from the stated order.

The controlled test does not show natural fd reuse or an attacker. Descriptor
lifetime, process ownership and coordination must prevent unintended close and
reuse; checking flags alone does not fence races. Poll errors mean observation
failed, not that revocation or input release was confirmed. The prototype is
still unsafe and the red test must not be merged as a normal passing suite.
No actual cancellation, X input, key-up, task success or MAP01 was tested.

The `raw.zip` SHA-256 is
`f4f143c30cda6b694b0494836ceba47cbb235bfb737f497646f08e1a69594fb7`.
It contains pre-run conditions, source base and diff, status, output and exit;
its members passed an integrity check. Image digest and flags are recorded
conditions, not independently attested by the captured unittest output.
