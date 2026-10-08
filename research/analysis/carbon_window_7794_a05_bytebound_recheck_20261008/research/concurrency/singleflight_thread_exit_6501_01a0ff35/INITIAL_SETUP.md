Before any matrix freeze/run, the first ordinary construction command
`python -B -m unittest -v test_mechanism` exited 1: two tests passed and the
early-rejoin test errored after its three-second barrier deadline. The tool
transcript is retained in this chat (`8e0545`); exact separate process byte streams
and UTC endpoints were not captured for that first command. They are not invented.

The initial scaffold awaited the rejoin under the candidate policy before opening
the gates, assuming the desired refusal. The deliberately broken candidate instead
started a second callable and blocked; both the read and cleanup observed the
authored barrier TimeoutError. All callable waits were bounded and the command
terminated. The scaffold was corrected to observe request/entry state, release
every actual gate regardless of outcome, and always shut down the executor.
This is a construction failure, not a consumed matrix result or cancellation proof.

A separately captured RED regression after that scaffold correction tests the
same intended exclusion without presupposing it. The actual eight-condition
matrix starts only after source/oracle/freeze publication in the local Git history.
