# Binary witness-root redundancy proof

Let each actor class be assigned an m-bit codeword, one bit per operationally independent binary provenance root.

## No fault
Exact classification requires only distinct codewords, equivalently minimum Hamming distance at least 1. Five classes require at least five codewords, so 2^m >= 5 and m >= 3. A 3-bit code supplies at least five distinct words.

## One known compromised root (erasure)
If the compromised coordinate is known and discarded, every pair of actor codewords must remain different after deleting any one coordinate. This holds iff every pair differs in at least two coordinates, i.e. minimum distance >=2. Three binary roots cannot encode five pairwise-distance>=2 words (exhaustively checked); four can.

## One unknown malicious root (Byzantine bit error)
If any one root may lie and its identity is unknown, the verifier receives a word within Hamming radius1 of the true actor codeword. Exact recovery requires the radius-1 balls of different actor codewords to be disjoint, equivalently minimum distance >=3. Five roots cannot host five such binary codewords; six can. Thus exact five-class attribution under one unknown malicious binary root needs at least six operationally independent roots in this model.

The bound is about independent witness channels. Shared custody, common-mode compromise, replay, stale scope, or unauthenticated bits can only weaken the effective distance.
