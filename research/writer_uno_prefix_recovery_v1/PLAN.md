# Writer UNO prefix recovery v1

H: Sender telemetry is insufficient; a Writer suffix recovery may proceed only from a fresh UNO observation bound to the same RuntimeUID/URL/text and the same current X11 XID/focus.

T: Two documents A=`book`, B=`bookk`; desired A=`bookkeeperoffice`. Compare weak text-only recovery against bound recovery across six conditions: fresh, close/reopen same URL (RuntimeUID changes), wrong-document observation, focus drift after binding, expired observation age, and text changed after observation. Development first; freeze source before retained experiment. XTest suffix uses 12 ms/character. Post-effect text comes from a separate `/usr/bin/python3` UNO process.

D: Bound recovery must complete fresh exactly and inject zero input for all five faults. Weak comparator must expose unsafe acceptance/effect for the same faults. Every trial must end with empty physical input. No blind retry.

C/U: UNO is a research application oracle/control plane, private Xvfb/Openbox only. Observation-to-input atomicity is still not proven. No Wayland/Windows/macOS/IME/model/token claim.
