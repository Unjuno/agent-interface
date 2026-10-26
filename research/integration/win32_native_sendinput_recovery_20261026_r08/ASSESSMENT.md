# R08 assessment — recovery, generation fence, and fixture task passed; oracle receipt rejected

The recovery phase passed: the blocked producer was retired, the held SHIFT was released in 16.742 ms under the 3 s deadline, and a separate same-generation native readback confirmed key-up. The old fixture exited cleanly. A distinct process and target generation were then created. The focus-only stale-generation dispatch, now schema-valid, was refused with `TARGET_GENERATION_CHANGED` before input.

The compiled public caller made one action on the fresh generation. The fixture recorded one click, the six `office` character events in order, and one save with the exact effect `{saved:true,text:"office",clicked:true}`. The post-dispatch observation was fresh and native readback found SHIFT, CTRL, S and left button all up. The new fixture exited cleanly and foreground restoration passed.

R08 still fails the frozen pass gate: the server rejected the configured oracle ID because it was not 32 lowercase hexadecimal characters, leaving `task_success=null` and the task-effect receipt unknown. The action-level release flag also was read from the wrong nesting level by the runner's scorer, despite the raw terminal action and native readback showing verified release. No independent task-success claim is made. This first outcome is immutable; R09 corrects the ID and audit field without editing R08.

Raw and preregistration hashes are independently verified. No AppServer model, WSLc, Docker, or task replay was used.
