# Separate stderr custody supplement

The original packet candidate remains c513bf6c736a8bbaee296ebbc2551e163fd283b43245996612f949453157833f. Its new own-peer counterexample returns after 512 bytes of stderr but times out with a live peer after 1 MiB. Both owned peers are retired in cleanup.

Separate private candidate 3a784bc3d1d68876871ac9425adc245026c208e36041a12f0eddd84e1334d1a1 adds binary stderr draining with a 65536-byte retained tail. Source-qualified ordinary actual-Python-peer checks cover ASCII and invalid UTF8 output at 512 bytes and 1 MiB, exact drained/tail counts and reader retirement. Two further own peers preserve Japanese echo and malformed-JSON error custody. These distinct scopes are not pooled into a computer-control PASS.

The first invalid-byte fixture generated a non-ASCII bytes literal and exited with SyntaxError; its first intent/journal are retained separately, and it is not used to judge the candidate. The corrected fixture uses bytes([255]). Raw copies retain original bytes; .jsonl receives a .txt suffix for inert storage.

Production adoption, source-owner agreement, ambiguous Thread-start recovery, descendants/inherited handles, blocked I/O and hard total deadlines remain unresolved. Binary drain requires the actual Popen stderr TextIOWrapper.buffer; alternate factories are not qualified. The bounded tail limits retained bytes, not total peer output or resource lifetime. No formal allocation, model or GUI/input task ran.
