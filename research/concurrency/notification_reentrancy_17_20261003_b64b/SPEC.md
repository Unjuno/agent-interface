# One finite ordinary notification reentrancy boundary — FINAL-v5

Parent #17/#59, actual worker01a0ff52-b64b. Prior native4 of7003 and formal
retry graph7029 remain immutable and consumed; neither is replayed. This new
constructor-free unit construction exercises actual wait_notification source
against a same-client nested consumer, which prior tests did not exercise.
It does not adopt the private comparator or repair a production source.

H: the baseline holds a reentrant Condition while iterating the live deque and
deletes a selected numeric index after callback. A callback may use the public
wait_notification method to consume that same selected object before returning.
Then a true callback may return the same already-consumed A twice and remove
unrelated B; a false callback may expose deque-iteration mutation. The retained
outside-Condition/identity-check comparison should refuse stale selection and
retain unrelated B in this finite one-nested-consumption schedule.

T: exactly six FIRST ordinary cells: baseline/outside × healthy/reentrant-true/
reentrant-false. A and B are distinct ordinary rich dictionaries, initial deque
[A,B], actual threading.Condition default RLock, closed=False, timeout=0.
Healthy callback is pure identity selection of A. Reentrant callbacks consume A
once using the SAME client's public method with a pure identity predicate and
timeout=0, then return True or False respectively. They never touch private
queue contents themselves, append new data, delay, spawn threads or loop.
The subjects are complete pinned modules loaded without constructing a client;
__new__ initializes only the actual method's Condition/deque/closed dependencies.
No fake method implementation, mocked clock, native peer, reader or process
factory. Record exact returned object identities, all rich values, callback and
nested-return order, remaining queue, exceptions, pins and terminal condition.
One container collector invocation and a separate frozen saved-only reader.

D: baseline healthy and outside healthy must each return A once with B retained.
Predicted baseline reentrant-true returns A both inside and outside and drops B;
baseline reentrant-false returns first RuntimeError/deque mutated during
iteration with B retained. Outside reentrant modes truthfully TimeoutError/no
outer result, inner returns A once and B remains. Preserve actual first rows;
missing source/trace/resource, unexpected exception/control or output cap
failure is STOP/HOLD and later phases stop. No identical cell retry, threshold
change or source repair after this execution. A saved-only independent literal
implementation verifies all six rows and >=12 effective copied contradictions.
Baseline counterexamples are evidence, not source gates to be silently relaxed.

C/U: an explicit reentrant callback schedule is allowed by the callable API but
known normal callers use pure comparisons; no actual production occurrence is
established. Comparison may change callback scheduling, matching priority and
finite recovery;7029 retains its retry-starvation counterexample and no general
recovery guarantee is restored here. No call-entry immutability, concurrent
arrival, equality-alias/Boolean-ID, actual client constructor, journal/wire,
real server/model/GUI/input/physical release/task effect or efficiency proof.
Timeout0 selects deterministic source behavior, not measured latency. Object
identity integers and A/B labels are local dimensionless identifiers, not
portable capabilities. UTC is provenance; no uncertainty interval is invented.

Resources: sole owned guest research-6695-docker-01a0ff52, fixed cached Python
digestdddfd7e0…,linux/arm64,privateEngine only. New own source/output directories,
read-only source/root,networknone,nonroot,CPU0.25,memory128MiB,swap0,pids32,
tmpfs8MiB,actual cgroup readback. One active container, no native subject peers.
Each CPU child12s fallback, outer phase30s, saved output262144B. No image pull,
new worker or shared/apply/main lease. Preserve containers/results/image, then
stop own guest after terminal reconciliation. GlobalN/commondeadline unknown
and unextended. Source/send/EOF/reader/codec/journal owners remain unchanged.

Preexecution context correction: maina216324b merged6955 close-only retirement.
Current baseline6508B/SHA2290f2f8…, private outside7137B/SHA98cdae09… now
shares that whole module except wait_notification. Old baseline/comparator and
first pin mismatch remain, cells0 at correction5969254478. The baseline wait
AST and outside wait AST each equal their historical counterparts. close is not
invoked; constructor/reader/send/source owners remain untouched.
