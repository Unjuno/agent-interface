# Post-formal mutation check

`supplemental_mutation_controls.py` runs after the frozen A02 pair and is not
part of `FREEZE.json`. It imports the already frozen independent `audit.py`,
loads the preserved candidate output, and checks four adversarial record
mutations. It does not invoke candidate or auditor command-line programs and
does not modify the frozen outputs.

The four controls reject (1) the stale position and anchor that a deleted
`surface_origin → screen_position` edge could leave behind, (2) a stale enabled
claim after a mode-branch mutation, (3) acceptance of an event from the prior
object generation, and (4) a CURRENT position claim with incomplete source
coverage. Result: `SUPPLEMENTAL_MUTATION_CONTROLS_PASS 4/4`.
