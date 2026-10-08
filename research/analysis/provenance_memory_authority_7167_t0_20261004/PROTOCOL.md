# Frozen protocol

## H / T / D / C / U

**H.** In this finite provenance contract, source-bound memory records retain
their original authority class through storage, exact-duplicate application
content consolidation, and retrieval. Application content, model hypotheses,
derived summaries, and records with missing source do not become active
user-authorized intent; legitimate descriptive recall remains available.

**T.** Run `candidate.py` exactly once on the 10-record fixed synthetic corpus.
Then run the independently authored `auditor.py` exactly once. The auditor
reconstructs the stored records, summaries, source-ref projections, and active
user-intent set from the fixture, and injects four corruption controls:
promote application instructions, drop summary source references, resurrect a
superseded user revision, and trust a record with missing source.

**D.** `PASS_METHOD_SCOPED` requires exact reconstruction of all records and
retrieved rows; exact source/origin preservation; only the highest revision
per user-instruction key active; zero non-user/derived/unknown authority
promotion; and rejection of all four mutations. Any mismatch is
`FAIL_METHOD`.

**C.** A simpler source label attached to each retrieved record may already
prevent these finite escalations without a broader object-memory architecture.
Conversely, downstream model behavior may ignore correct labels entirely.

**U.** This tests only deterministic data transformations and a stipulated
authority policy. It is not a prompt-injection, model-compliance, live
vulnerability, security-boundary, user, or GUI test. Source authenticity and
label correctness are assumed inputs. No authority is granted by retrieval.

## Runtime and one-shot procedure

No network, model, GUI, container, external data, or filesystem side effects
are required. Host Python standard library is sufficient; using a container
would not exercise any container-specific property. Pre-freeze unit tests are
construction evidence only. After source freeze commit and the GitHub issue
preregistration comment, invoke candidate once to `formal_01/raw.json`; only
after exit code 0, invoke auditor once to `formal_01/audit.json`. No retries.
