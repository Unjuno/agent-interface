# Win32 supervisor real pipe blocked-send R04

This fresh R04 uses the pinned current-main `OperationCancellationSupervisor._exchange_helper` and a real Windows `multiprocessing.Pipe`. An owned Job Object contains a gated worker and a separate non-reading peer. To force pipe backpressure, the diagnostic request includes 8 MiB of padding; the identity reader is a fake constant and cleanup grace is zero. No helper capable of input release is run.

The exchange remained blocked when observed after its 200 ms deadline. After the peer was terminated, the exchange returned `BrokenPipeError`, marked the helper unavailable, and the worker and peer exited. Exact source, environment, traces, result, empty output streams and hashes are retained. Process inventory after completion found no worker/peer PID remaining. This is one observed schedule, not a deadline guarantee or a claim that normal-sized supervisor requests will block. The process identity reader was not verified natively.

This does not prove input release, observer neutrality, rejection of a message accepted before termination, or that a replacement owner is safe. No GUI, game, model, native keyboard/mouse input, WSLc or Docker was used. A future fix needs bounded transport or exact helper retirement plus retained UNKNOWN custody; a timed-out thread alone is not retirement. A rerun needs a fresh output directory.
