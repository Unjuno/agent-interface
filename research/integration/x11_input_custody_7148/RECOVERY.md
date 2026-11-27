# X11 input-custody candidate safety HOLD — closed PR #7148

Source PR [#7148](https://github.com/Unjuno/agent-interface/pull/7148) was
closed unmerged on 2026-10-05. Its unchanged V4 head is
`ed7bb24e45fac16114e1247e00c8ed86cebda5c8` (tree
`2e7d32a21374070a8809a924f2708d4b6eccc88d`). The author's final disposition
explicitly suspends content review and holds adoption/application. This record
preserves the safety outcome; it does not promote the candidate.

## H/T/D/C/U

- **H:** A release path must not clear input custody merely because an UP was
  emitted or because a device-state query returned no pressed buttons. Routing
  to a different XTEST ClientPointer, device reassignment/ABA, or unreadable
  state can leave the original input down while the candidate reports verified
  completion.
- **T:** The source PR reports 57 selected V4 methods passing normally and
  under `-O`, plus 176 endpoint rows. Follow-up source-supported constructions
  then falsified the safety inference: an UP can be routed to another
  ClientPointer, and a valid XI2 inventory can suppress unreadable button state
  to zero while button 9 remains modeled as held. The original green suites
  and failures remain historical; no producer or formal allocation was rerun
  for this rescue.
- **D:** Preserve as a negative qualification and adoption HOLD. Do not merge
  the nine-path runtime/workflow/test patch from #7148. Prior content offers or
  votes do not transfer to any future repair.
- **C:** These are source-supported constructions and explicit inert access
  profiles, not evidence that a particular native XACE deployment or physical
  device exhibited the condition. The separate N02 Xvfb comment describes one
  injected missing-UP baseline; it does not qualify V4, device identity, or
  application/task effects. No latency, safety, or universal release claim is
  established.
- **U:** A future candidate must bind release and readback to the same owned
  device generation, treat denied/incomplete reads as unknown rather than
  all-up, and independently qualify routing and competing-client cases. The
  public continuation package declares 16 omissions; a prior capsule part is
  unconfirmed, and N02's full artifacts remain local. Full source-reader
  reproduction is therefore not claimed.

## Evidence references

- [Author's V4 suspension and counterexamples](https://github.com/Unjuno/agent-interface/pull/7148#issuecomment-5973813117)
- [Public continuation evidence, part 1](https://github.com/Unjuno/agent-interface/pull/7148#issuecomment-5973818443) and [part 2](https://github.com/Unjuno/agent-interface/pull/7148#issuecomment-5973821630)
- [N02 injected Xvfb baseline summary](https://github.com/Unjuno/agent-interface/pull/7148#issuecomment-5973902271) and [saved-reader correction](https://github.com/Unjuno/agent-interface/pull/7148#issuecomment-5973922245)

No candidate source or archived executable was copied or run. The current-main
review found no existing `#7148` disposition entry; this note is navigation and
safety history only, not a fresh experiment or an assertion about current-main
runtime behavior.
