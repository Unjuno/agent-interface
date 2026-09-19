# Writer UNO durable recovery v1

H: the retained bound Writer suffix recovery can be serialized durably to native ODT, while bound fault refusals never durably append the recovery suffix.

T: six fresh private Xvfb/Openbox/Writer sessions after source freeze, fixed order `fresh, stale_uid, wrong_doc, focus_drift, stale_age, text_changed`. A starts `book`, B `bookk`, desired A `bookkeeperoffice`. The recovery decision/binding matches the retained PR #280 semantics. After recovery/refusal, exact current UNO components are `store()`d as explicit fixture finalization, LibreOffice is terminated, and a separate non-UNO ZIP/XML scorer reads the ODTs. No arm reruns.

D: fresh must have nonzero recovery input and exact durable A=`bookkeeperoffice`, B=`bookk`. Each fault must inject zero recovery input; durable A remains `book`, except `text_changed` retains injected `boox`; B remains `bookk`. Every ODT must pass ZIP CRC, physical input must be empty. PASS does not claim X11 save-key semantics or close the post-guard TOCTOU race.

C: UNO store is fixture finalization and may itself fail; LibreOffice buffering/termination could hide persistence bugs; XML text extraction is independent of UNO but ODT-specific.

U: private X11/Writer/lowercase ASCII only; no reliability population, Unicode/IME, Wayland, Windows/macOS, model/token or general Office claim.
