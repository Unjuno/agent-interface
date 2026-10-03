# Integration handoff for existing source owners

The consumed A02 pins #6965 fbd804e549b589e7e7e692ab4f89183d21451ca7 and close V1 #6955 31f10e660d2e7e13d8fe05c9a56d3f3c5e71f324. Do not replace the public client with either full donor snapshot.

1. Send owner: keep the common request/notify deadline, nonblocking writes and uncertainty quarantine. Pass the deadline only to sent _record, acquire the journal mutex for its remaining time, and release in finally. A timeout before any pipe write belongs outside the partial-write poison path. A02 empirically tests request only.
2. Close owner: preserve newer V2 dd322c2d355a4ab4d917d3216a5fe08ab8b83eff reader.is_alive refusal before journal closure. A02 provides no execution qualification for V2.
3. UTF-8 owner #6991: preserve explicit Popen encoding and the compatible-factory boundary.
4. Keep fresh main's no-drain EOF, receive/cache behavior and separately owned response-ID changes; pin and review the resulting exact composition.

Journal write/flush and serialization remain synchronous and unbounded. Received journaling still precedes response publication; condition locks and arbitrary predicates remain separate. Sent rows are intent, not server acceptance. Close has separate stage budgets and driver closure is not close-alone efficacy.

#6965's independent Windows CPython 3.12+ default-Popen qualification remains: LF framing, large records, backpressure/partial writes, typed uncertainty and later refusal on the revised composition; older-runtime compatibility also needs disposition. This small Linux request-mutex witness does not qualify those paths or close #59/#57.
