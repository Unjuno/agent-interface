# R554: shutdown wait and late startup

On base bf6675d1d588b5071d84a9f5a8516a1739514a39, a draft waits up to one second to acquire lifecycle custody after an initial busy close. In a pinned, isolated fake-owner container, four controls passed in both normal and optimized Python. A fifth deliberately gated startup beyond a 50 ms shutdown wait: shutdown returned UNKNOWN, then startup resumed and the child remained alive. That case failed in both modes; fixture cleanup retired the child. See raw.zip for preregistered conditions, candidate diff, output and exit codes.

The wait only bounds lock acquisition. It does not establish bounded shutdown, persistent custody, input release, real GUI effects, or MAP01 behavior. The candidate and red regression remain draft research and must not be merged as a complete fix. A custodian independent of the returning shutdown path or another proven handoff must handle the late child, including permanent stalls and parent death.
