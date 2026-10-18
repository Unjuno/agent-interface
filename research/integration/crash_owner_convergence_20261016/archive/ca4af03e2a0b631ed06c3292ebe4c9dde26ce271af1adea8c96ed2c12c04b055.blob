# A27 normal receipt generation-binding plan

Start the real `InputOwnerProcess` on a fresh private TCP-disabled Xvfb display with no input admitted, close it normally, and verify the fsynced owner receipt contains the same PID and `/proc` start ticks published by its process handshake. Pass the same ready identity through `verify_owner_process_recovery` and require the normal verified close receipt to be accepted after the service exits. This specifically checks compatibility after adding service-generation identity to normal receipts.

No physical input, game, model, or scored control action. One fresh construction allocation, one invocation, no retry. Xvfb is isolated with a private temporary `/tmp` namespace.
