MODES = (
    "requester_only",
    "all_owner_conjunction",
    "scoped_delegation",
    "deny_all",
)

def grant(principal, resource, effect, recipient, epoch, state="ALLOW", authentic=True):
    return {
        "principal": principal,
        "resource": resource,
        "effect": effect,
        "recipient": recipient,
        "epoch": epoch,
        "state": state,
        "authentic": authentic,
    }

def delegation(principal, delegate, resource, effect, recipient, epoch, authentic=True):
    return {
        "principal": principal,
        "delegate": delegate,
        "resource": resource,
        "effect": effect,
        "recipient": recipient,
        "epoch": epoch,
        "authentic": authentic,
    }

def trace(trace_id, resource, owners, effect, recipient="app", requester="A",
          owner_epochs=None, grants=None, delegations=None, safety_action=False,
          owner_set_status="KNOWN"):
    return {
        "trace_id": trace_id,
        "resource": resource,
        "owners": owners,
        "owner_set_status": owner_set_status,
        "requester": requester,
        "effect": effect,
        "recipient": recipient,
        "owner_epochs": owner_epochs or {owner: 1 for owner in (owners or [])},
        "grants": grants or [],
        "delegations": delegations or [],
        "safety_action": safety_action,
    }

TRACES = {
    "private_a_read": trace(
        "private_a_read", "private-A", ["A"], "READ",
        grants=[grant("A", "private-A", "READ", "app", 1)],
    ),
    "shared_read_a_only": trace(
        "shared_read_a_only", "shared", ["A", "B"], "READ",
        grants=[grant("A", "shared", "READ", "app", 1)],
    ),
    "shared_read_both": trace(
        "shared_read_both", "shared", ["A", "B"], "READ",
        grants=[grant("A", "shared", "READ", "app", 1),
                grant("B", "shared", "READ", "app", 1)],
    ),
    "private_a_write": trace(
        "private_a_write", "private-A", ["A"], "WRITE",
        grants=[grant("A", "private-A", "WRITE", "app", 1)],
    ),
    "shared_a_only": trace(
        "shared_a_only", "shared", ["A", "B"], "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1)],
    ),
    "shared_both_grant": trace(
        "shared_both_grant", "shared", ["A", "B"], "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1),
                grant("B", "shared", "WRITE", "app", 1)],
    ),
    "shared_conflict": trace(
        "shared_conflict", "shared", ["A", "B"], "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1),
                grant("B", "shared", "WRITE", "app", 1, state="DENY")],
    ),
    "shared_revoked": trace(
        "shared_revoked", "shared", ["A", "B"], "WRITE",
        owner_epochs={"A": 1, "B": 2},
        grants=[grant("A", "shared", "WRITE", "app", 1),
                grant("B", "shared", "WRITE", "app", 1)],
    ),
    "shared_forged": trace(
        "shared_forged", "shared", ["A", "B"], "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1),
                grant("B", "shared", "WRITE", "app", 1, authentic=False)],
    ),
    "unknown_owners": trace(
        "unknown_owners", "shared", None, "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1)],
        owner_set_status="UNKNOWN",
    ),
    "shared_delegated_write": trace(
        "shared_delegated_write", "shared", ["A", "B"], "WRITE",
        grants=[grant("A", "shared", "WRITE", "app", 1)],
        delegations=[delegation("B", "A", "shared", "WRITE", "app", 1)],
    ),
    "delegation_wrong_recipient": trace(
        "delegation_wrong_recipient", "shared", ["A", "B"], "WRITE",
        recipient="external", grants=[grant("A", "shared", "WRITE", "external", 1)],
        delegations=[delegation("B", "A", "shared", "WRITE", "app", 1)],
    ),
    "delegation_revoked": trace(
        "delegation_revoked", "shared", ["A", "B"], "WRITE",
        owner_epochs={"A": 1, "B": 2},
        grants=[grant("A", "shared", "WRITE", "app", 1)],
        delegations=[delegation("B", "A", "shared", "WRITE", "app", 1)],
    ),
    "disclose_wrong_recipient": trace(
        "disclose_wrong_recipient", "shared", ["A", "B"], "DISCLOSE",
        recipient="external", grants=[grant("A", "shared", "DISCLOSE", "external", 1),
                                       grant("B", "shared", "DISCLOSE", "app", 1)],
    ),
    "shared_layout_both": trace(
        "shared_layout_both", "shared-window", ["A", "B"], "LAYOUT",
        grants=[grant("A", "shared-window", "LAYOUT", "app", 1),
                grant("B", "shared-window", "LAYOUT", "app", 1)],
    ),
    "emergency_release": trace(
        "emergency_release", "input-lease", ["A", "B"], "RELEASE",
        grants=[], safety_action=True,
    ),
    "cancel": trace(
        "cancel", "input-lease", ["A", "B"], "CANCEL",
        grants=[], safety_action=True,
    ),
}
