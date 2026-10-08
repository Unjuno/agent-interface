# Conditional query equivalence and space accounting

## Variables

| Symbol | Meaning (Japanese) | SI / representation unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| B | 入力byte数 | dimensionless byte count, 1 byte=8 bits | len(data) | 0..67,108,864 | integer scalar |
| N | LFの個数 | dimensionless count | count of0x0a | 0..B | integer scalar |
| j | prefixの通し番号 | dimensionless | empty prefix0, j-th LF endpoint thereafter | 0..N | integer scalar |
| o_j | prefix末尾offset | byte count | o_0=0; position after j-th LF | strictly increasing after0; <=B | integer scalar |
| h_j | prefixハッシュ | 32-byte string, not physical SI quantity | SHA256(data[0:o_j]) | trusted immutable data; usual hash assumption for integrity claims | byte vector |
| q_j | 次のsequence | dimensionless count | j+1 | 1..N+1 | integer scalar |
| w | packed entry長 | byte count | 8+32=40 | '<Q32s', no padding | integer scalar |
| S | packed payload長 | byte count | w(N+1) | excludes object headers and input | integer scalar |
| M | pageの最大件数 | dimensionless count | max_records | strict Python int1..128 | integer scalar |

## Proof from construction to query

The empty prefix entry stores offset0, the digest of empty bytes and implied next sequence1. Therefore it agrees with the exact original table at j=0.

Assume agreement after j complete LF-terminated slices. The next `find` locates the next0x0a after o_j. Updating the same SHA256 state with data[o_j:o_(j+1)] yields SHA256(data[0:o_(j+1)]). The next packed entry stores that exact offset and32-byte digest; converting digest bytes to lowercase hex gives the original hexdigest. Its ordinal is j+1, hence its reconstructed next sequence is j+2, identical to original sequence increment. By induction, every entry0..N agrees. Empty or invalid JSON lines are still LF boundaries in both constructors; neither constructor certifies that prefix as semantically valid. Bytes after the last LF affect full snapshot digest but add no prefix entry, exactly as in the original.

Offsets strictly increase, so lower-bound binary search returns an entry exactly when the queried integer offset is an indexed boundary. Otherwise KeyError becomes Mapping.get's default None, matching the original mapping's missing-boundary result. All admitted read offsets are strict Python integers due the unchanged read method; external direct mapping lookup for noninteger aliases is outside this proof.

Both preparations first enforce identical data/stream/budget conditions. Then data,stream_id,max_bytes,full digest and every allowed prefixes lookup agree. `read` and `metadata` are inherited unchanged, and therefore see identical branch conditions, parser inputs, exception conditions, returned record values, tail labels and next cursors for every request in their declared contract. This proves functional equivalence under trusted immutable data and valid preparation; it does not prove safe arbitrary construction, capture coherence or source authenticity.

## Space and work

Every packed entry has8 offset bytes and32 digest bytes; ordinal reconstructs sequence without storing another integer. Thus S=40(N+1) exactly. Dimensional check: byte/entry × entry count = byte. For N=8192, S=327720 bytes, versus1048576 input bytes. This is table payload only; process memory, Python headers, build buffer and tracer storage are separate.

Preparation counts LF over B bytes and visits each complete slice once for hashing, so its work is O(B+N) with an added full count pass versus the original. Lookup becomes O(log(N+1)) unpack operations rather than expected constant-time dictionary lookup. It also allocates a transient tuple and hex digest at each successful lookup. Converting the build bytearray into immutable bytes temporarily retains both representations. Hence neither elapsed-time improvement nor peak-memory improvement follows from the payload formula. They require the separately fixed measurements; an unfavorable timing gate must remain HOLD.

## ERROR CHECK

Zero LF -> one40-byte empty entry; one final LF -> exactly one extra entry; incomplete tail contributes only full digest. uint64 offset capacity exceeds the inherited67,108,864-byte input limit. Little-endian standard width avoids native padding/ABI dependence. No floating-point arithmetic enters offsets/sequences. External source/hash authenticity, concurrent use and model utility are not implied.
