# Actual native game construction: STOP before input

The final outcome is **STOP_NO_ADVANCING_GETTER_CLOCK**, with the attack
condition **NOT_RUN**. The writable-CWD repair lets a real ViZDoom1.3.1 basic
scenario render in isolated X11, but seven getter snapshots all return tic14
over1,006,493,992ns. This construction establishes neither a current episode
clock nor input effect, per-key release, positive useful feedback or R134/v39.
The first exit139 and the later STOP2 remain first outcomes, not successful
formal results. See [RETAINED_READING.json](RETAINED_READING.json).

## Question and scope

This was a new bounded environment/input construction under
[claim5966043438](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5966043438),
using inspected main`fb556b3d8bf5bae54a1f23b89fe2c2b5a2685df7`.
It did not reuse the old MAP01/live04/matched-recovery allocation or threat save.
The packaged2704byte **basic.wad** names map01 internally; it is not the
Freedoom MAP01 task. No model, game API action selection, save/load/pause,
object/sector/automap labels, shared display/runtime/GPU or peer allocation was
used. The intended two conditions were a fresh seed7 no-input control and a
fixed1000ms native Space hold, with an invalid control stopping before attack.
The literal controller does not adapt to privileged game variables. Recorder
data are used only for the engineering control-validity stop, not action choice.

The four unchanged retained input/lease modules and their repository source
hashes are in [source-pins.json](source-pins.json). The native driver is an
authored small construction harness, not session-v13/v39 or a rich-model agent.
Both ordinary native attempts use exactly the same five executable source
hashes, seed, timing and gate. No threshold was changed after the results.

## First failure and one material repair

One private image build completed, using pinned Python base and nine requested
package versions. ViZDoom's pygame-ce dependency resolved to2.5.8 during build;
the effective package/wheel/DPKG hashes and immutable image were fixed before
either native attempt. Do not describe the networked apt/pip build as a
preregistered, bit-for-bit reproducible dependency resolution.

An initial metadata command had a Python parenthesis SyntaxError; its exact
stderr remains in [metadata.stderr](receipts/metadata.stderr). The corrected
metadata-only reader passed, without constructing or starting a game.

Native01 ran with a read-only root and its default CWD. It exited139, non-OOM,
with `Failed to create ./_vizdoom/ directory: Read-only file system` in
[first native stderr](receipts/native01/command-06.stderr).
RUNTIME.json and the empty Xvfb log exist; no first screenshot/control ROW was
saved. Python finally did not provide cleanup records. The original fault's
exact native stack location and how far game initialization reached are UNKNOWN.
The caller/container termination and removal were observed; neither proves a
physical-input release. Attack was not run.

After that STOP, one **display-free, no-init** constructor/configuration probe
with CWD=/tmp passed all stage marks and close. Its source and stdout are retained
as [constructor_probe.py](constructor_probe.py) and
[constructor-probe01.stdout](receipts/constructor-probe01.stdout).
This isolated the writable-CWD requirement enough to justify one necessary
ordinary regression, disclosed in
[repair5966137697](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5966137697).
The material repair adds `--workdir /tmp`; faulthandler diagnostics were enabled.
Root/source/image/controller remain unchanged. This was ordinary self-repair,
not a consumed formal replay or changing only an execution ID to obtain success.

## Repaired control and the remaining gate

Native02 initialized the actual game and captured its visible window, class
`vizdoom`, title `VIZDOOM 1.3.1 (ZDOOM 2.8.1+)`, observed focus4194320.
The no-input control saved seven getter snapshots: tic before/after14,
ammo50, kills0, deaths0 and dead=false. They span just over1s of real monotonic
time. The two saved encoded PNGs differ, and visual inspection shows a changed
weapon pose. Such render change is not an independently measured game clock,
positive task progress or proof of full async-state freshness.

The fixed control gate required increasing episode tics and therefore STOPped
with exit2. Its attack is NOT_RUN. The private X11 server keymap is all-zero in
both independent queries; no input-admission event exists. An empty-input owner
release returned verified=true, owner close returned with its thread no longer
alive, game/client close returned, and the actual Xvfb process was waited/reaped0.
These observations exercise an empty control, not an explicit held-key release.

Tagged upstream source reading confirms that getEpisodeTime delegates to the
controller's stored game-state MAP_TIC field. The API documents state update
through advance_action, but no such refresh is exercised by this driver. See
[upstream provenance](UPSTREAM_READING.json),
[Game source](https://raw.githubusercontent.com/Farama-Foundation/ViZDoom/1.3.1/src/lib/ViZDoomGame.cpp),
[Controller source](https://raw.githubusercontent.com/Farama-Foundation/ViZDoom/1.3.1/src/lib/ViZDoomController.cpp)
and [API documentation](https://vizdoom.farama.org/main/api/python/doom_game/).
The evidence is consistent with stale shared-state getters without refresh;
it does **not** prove engine freeze, general ViZDoom failure or a defect in
the currently deployed session-v13 scorer. Bracketing equal cached tics alone
cannot establish measurement freshness. A later source-qualified calibration
must separate state refresh, live engine progress and API action authority;
the original control gate will not be retroactively changed to PASS.

## Resources, evidence and review

Immutable Linux/arm64 image
`sha256:93ef9169b70d152291972b652bde109d15868d25f65e1110a817b1f63ead886f`,
observed size368,109,012bytes, contains ViZDoom1.3.1 and Python3.12.15.
The actual runtime records cpu.max100000/100000, memory.max805306368,
pids.max96. Source/root are read-only; /tmp is private64MiB tmpfs and output
is a guest32MiB tmpfs, with source and output mounts distinct. Runtime network
is none; build network was used for dependencies. A40s outer container command
watchdog with5s kill tier is configured. These are observed settings and short
cooperative executions, not adversarial enforcement or hard-time-bound proof.
Both runtime container states are terminal/non-OOM and removed. Own guest
`research-6695-docker-01a0ff52` was observed stopped; the cached image and stopped
build intermediates remain preserved. No shared resource or application lock
is held. Other workers' state and global host-load isolation are not asserted.

The original private commands/inspection data remain preserved. Public receipt
copies replace only the author's absolute source-root mount with literal
`{OWN_SOURCE_ROOT}` and bind original/derivative hashes in
[PUBLICATION.json](PUBLICATION.json). All unchanged copied logs and sources
remain byte-exact. The two native pin documents precede their own starts.
The original [read_retained.py](read_retained.py) is a separate, post-result
stdlib-only author reader over saved data; it imports no producer/runtime/game
library. A layout-adjusted public copy is available as
[read_public.py](read_public.py). It checks source/exit/clock/keymap/cleanup
joins and retains the STOP outcome; it is not a preregistered or nonauthor audit.

This is an inert archive plus one DOOM index row, with no active runtime,
workflow or default test-discovery change. Nonauthor content/combination and
actual-requirements/conditional-forward-application gates remain separate.
It provides a concrete writable-CWD repair and a counterexample to accepting
getter clock coherence as freshness in this construction. It does not close
#59/#57, supply useful-feedback/model/recovery/efficiency evidence, or authorize
replaying an old allocation.

The whole-archive whitespace check reported two unchanged raw build-log issues
(CR/trailing bytes and a final blank line). Those raw bytes stay intact; the
source/document-only diff check passes. No whole-archive whitespace PASS is
claimed. This is separate from evidence hashes and the observed native STOP.
