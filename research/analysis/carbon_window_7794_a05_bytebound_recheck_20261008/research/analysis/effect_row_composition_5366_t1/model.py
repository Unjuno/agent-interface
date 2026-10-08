"""Finite compositional effect-row gate; it never dispatches effects."""
CASES={
"pure_direct":dict(row=(),actual=(),approved=()),
"direct_read":dict(row=("read(ui)",),actual=("read(ui)",),approved=("read(ui)",)),
"polymorphic_network_instantiation":dict(row=("network(send)",),actual=("network(send)",),approved=("read(ui)",)),
"wrapper_masks_nested_write":dict(row=("write(file)",),actual=("write(file)",),approved=("read(ui)",)),
"branch_union_false_reject":dict(row=("read(file)","write(file)"),actual=("read(file)",),approved=("read(file)",)),
"native_unknown":dict(row=None,actual=None,approved=("read(ui)",)),
"remote_unknown":dict(row=None,actual=None,approved=("read(ui)",)),
"valid_transitive_read_observe":dict(row=("read(ui)","observe(screen)"),actual=("read(ui)","observe(screen)"),approved=("read(ui)","observe(screen)")),
"contained_effect_row":dict(row=("read(ui)",),actual=("read(ui)",),approved=("read(ui)","write(file)")),
}
def evaluate(case):
    row,actual,approved=case["row"],case["actual"],set(case["approved"])
    if row is None:return {"status":"EFFECT_UNKNOWN","admitted":False,"false_reject":False}
    admitted=set(row)<=approved
    safe_actual=actual is not None and set(actual)<=approved
    return {"status":"ADMIT" if admitted else "REJECT_UNDECLARED","admitted":admitted,"false_reject":bool(not admitted and safe_actual)}
