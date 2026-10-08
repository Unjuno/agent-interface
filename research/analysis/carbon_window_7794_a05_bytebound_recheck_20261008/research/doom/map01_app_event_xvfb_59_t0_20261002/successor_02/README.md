# Issue #59 T0 — X11 occupancy versus application delivery

This frozen construction experiment distinguishes a server-global keyboard
state witness from delivery of the corresponding key event to the currently
focused application. It uses one private Xvfb server, two minimal X11 client
windows, and XTEST-generated key events. It never touches a host display,
physical keyboard, game, or user application.

See `PLAN.md` and `FREEZE.json` for H/T/D/C/U and frozen gates. Formal results,
the independent raw-only audit, commands, environment identity, and hashes are
retained under `results/formal-02/` after the one-shot run. The predecessor
allocation-01 preflight STOP remains unchanged at the parent `results/formal-01/`.

## Scope

This tests an observability boundary relevant to Issue #59's held-input and
useful-effect accounting: whether `XQueryKeymap` true can be interpreted as
evidence that a particular focused application received the corresponding
KeyPress. It does not measure physical held duration, event handling by a real
game, useful task progress, model wait behavior, safety, or MAP01 efficacy.

Image: `map01-attack-onset-phase-a2:20260927-r2`, pinned in the freeze by
content digest. Run commands and container limits are in `RUN.json`.
