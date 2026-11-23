# R33 result — fixture failed before creating a window

**Disposition: `STOP_FIXTURE_DLL_NAME_TYPO_BEFORE_WINDOW`.** The frozen
allocation is consumed; it was not a runtime attempt and must not be rerun.

The fixture process exited during module import because a broad lowercase
`r32`→`r33` identifier replacement changed the Windows DLL name `user32` to
`user33`. No fixture window was created, no public MCP observation or dispatch
occurred, no recovery/task action occurred, and no process remains. The durable
fence remains clear. Exact stderr is retained.

No product behavior or task result is claimed. The next allocation must preserve
system DLL names and statically verify the fixture's Win32 library bindings
before launching its single fixture.
