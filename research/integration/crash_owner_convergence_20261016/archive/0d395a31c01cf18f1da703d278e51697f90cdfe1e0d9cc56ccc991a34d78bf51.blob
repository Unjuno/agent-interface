# A37: per-device held-key aggregation in private Xvfb

**H** — A process-owned core-XTest release will clear only its XTEST keyboard source; a same-key hold on Xvfb's separate synthetic slave keyboard will remain down in the virtual core keymap until that second device releases.

**T** — One private TCP-disabled Xvfb display and actual `InputOwnerProcess` V4 service. The owner sends XTest key `a` from `Virtual core XTEST keyboard`; a separate ctypes/libXi/libXtst connection discovers and opens the enabled `Xvfb keyboard` XI device and uses `XTestFakeDeviceKeyEvent` to press the same key. An independent XI2 AllDevices raw observer records source IDs and a core focus observer records KeyRelease/keymap. The second synthetic device is released after owner key-up, then owner closes normally. No `/dev/uinput`, physical device, GUI app, game, model, or shared X server.

**D** — `PASS_METHOD_SCOPED` if raw source IDs identify owner XTEST and the distinct Xvfb keyboard, the keymap remains down after owner source RawKeyRelease while the second device is held, then becomes up after the second device RawKeyRelease with a core KeyRelease observed and owner close receipt verified. `FAIL_METHOD_SCOPED` if owner release clears the global keymap while the second source remains held. `STOP` on device open, injection, event observation, or owner cleanup failure.

**C** — The Xvfb keyboard is a synthetic server device, not a physical keyboard. This tests per-device server aggregation only; it cannot establish real Xorg/Wayland physical input semantics or application behavior.

**U** — No live desktop, game, model, physical input, or task effect. The result can refine the distinction between XTest client identity and XI2 device-source identity, not resolve Issue #59's live MAP01 requirement.

One frozen candidate invocation, no retries. Allocation: `V39-XVFB-SECOND-DEVICE-HELD-KEY-A37-20261012-01`. A35/A36 established global core-XTest state and identical XTest source IDs across client connections; A37 tests a distinct XInput device source.
