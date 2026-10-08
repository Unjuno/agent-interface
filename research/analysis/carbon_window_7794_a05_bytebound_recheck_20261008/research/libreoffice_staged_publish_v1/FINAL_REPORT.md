# LibreOffice staged publish + Linux lease discovery v1

Status: **RETAIN staging as a no-authority work area; RETAIN inode-lease serialization for same-inode writers; FAIL staging+inode lease as a general pathname commit boundary.**

Immutable BASE: `ed04bba63813ddfa508912eaaadcdca87d59600b`. Issue #299.

## Rung A — staging separates GUI Save from authoritative target
Frozen pair passed. Stable staging save published `office/preview`. A target replacement occurring before the final publish check was detected and publication refused; the external workbook remained intact. Independent two-row audit passed.

This removes LibreOffice from direct write authority over the target during editing, but leaves a check→publish race.

## Rung B1 — target lease availability
First probe ID failed as a harness result: after acquiring a lease, the harness reopened its own leased pathname for SHA calculation and died on SIGIO 29. No science result was claimed.

Successor B1 removed the self-open. With Calc alive on staging only, `F_SETLEASE(F_WRLCK)` succeeded and remained `F_WRLCK` for 0.5 s with no SIGIO. Target inode/SHA stayed unchanged.

## Rung B2 — enforcement on same-inode writer
Separate writer attempted `open(target,'r+b')`. Lease owner received SIGIO; writer remained alive/not-done until release. Monotonic ns: writer open begin `551887613228`, lease release `551891360886`, open returned `551891411957`. Writer fd inode `262607` equaled leased inode `262607`.

## Rung B3 — publish while writer is blocked
Stable and race arms both saved staging through real LibreOffice/X11. In race arm controller held the old target lease, writer blocked, then controller published staging via temp+fsync+`os.replace`. Authoritative target inode changed from `263266` to `263398`. After old lease release, writer completed on fd inode `263266` — the old unlinked inode — while final pathname remained `office/preview`.

This is a valid linearization for an already-started open/write racer.

## Rung B4 — adversarial pathname replacement falsifies the general claim
While the target's old inode still held `F_WRLCK`, a separate process executed `os.replace(external.xlsx, target.xlsx)`. It completed **before controller publish** with no SIGIO. Path inode changed from leased `262745` to external `262876` and independently scored `external/replacement/external-marker/writer`.

Controller still had an eligible old leased fd and then published staging, installing inode `263512` and overwriting the external target with `office/preview`. Classification: **`LEASE_PATHNAME_RACE_FAIL`**.

Therefore Linux inode leases do not supply the required compare-and-publish authority over pathname replacement.

## H / T / D / C / U
**H.** Staging may isolate GUI effects and make an otherwise unavailable target lease usable; the lease may serialize writers through an old inode.

**T.** Private LibreOffice 25.2.3.2/Openbox/Xvfb, one frozen staged pair, lease availability probe, same-inode writer probe, one stable+race publish pair, and one pathname-replacement adversarial arm. First harness failure retained separately. No model or user data.

**D.** RETAIN staging for pre-publish invalidation and lease serialization of open/write races. FAIL staging+inode lease as general commit ownership because `os.replace` bypassed the lease and recreated stale overwrite.

**C.** Protection in B3 is explained by the waiting writer being bound to the leased old inode; it is not pathname serialization. B4 directly discriminates this explanation.

**U.** One Linux filesystem/container/app version; staging can alter document-path semantics; exact SHA/inode checks can be over-strict; no directory/FUSE/fanotify mediator, network filesystem, power loss or natural race-rate claim.

## Architecture consequence
An ordinary GUI Save can be made safer by staging, but a generic Agent Interface still needs **authoritative pathname/commit ownership or an application/effect-owner conditional commit** to close the final race. Old-inode guards are insufficient. If neither is available, fail-closed/escalation remains more defensible than claiming atomicity.

## Error check
Independent post-outcome audit: `True`, errors `[]`; three deliberate corruptions rejected.
