"""Independent finite denominator / raw suite audit for Issue #8399."""
import ast
import itertools
import sys

# Restated independently; this module does not import candidate.py.
legal_histories = []
for focus in (0, 1):
    for surface in (0, 1):
        for fresh in (0, 1):
            context = (focus, surface, fresh)
            legal_histories.append((context, ("OBSERVE", "ACT", "RELEASE")))
            legal_histories.append((context, ("OBSERVE", "REVOKE", "ACT", "RELEASE")))

record = ast.literal_eval(open(sys.argv[1], encoding="utf-8").read())
rows = record["suite"]
obligations = {
    (context[0], context[1], "REVOKE", "ACT")
    for context, history in legal_histories
    if any(history[i:i + 2] == ("REVOKE", "ACT") for i in range(len(history) - 1))
}
covered = {
    (context[0], context[1], "REVOKE", "ACT")
    for context, history in rows
    if any(history[i:i + 2] == ("REVOKE", "ACT") for i in range(len(history) - 1))
}
assert record["episodes"] == len(legal_histories) == 16
assert len(rows) == 4 and covered == obligations
assert len(rows) < len(legal_histories)

# Context-only and event-only controls each miss the joint interaction.
context_only = [(context, ("OBSERVE", "ACT", "RELEASE"))
                for context, _ in legal_histories]
order_only = [((0, 0, 0), ("OBSERVE", "REVOKE", "ACT", "RELEASE"))]
def detects_joint(suite):
    return any(context[:2] == (1, 1) and
               any(history[i:i + 2] == ("REVOKE", "ACT")
                   for i in range(len(history) - 1))
               for context, history in suite)
assert not detects_joint(context_only)
assert not detects_joint(order_only)
assert detects_joint(rows)

# Reset partitions two event lists; no order crosses the boundary.
reset_episodes = (("OBSERVE", "REVOKE"), ("ACT", "RELEASE"))
within_episode_pairs = {
    (episode[i], episode[j])
    for episode in reset_episodes
    for i in range(len(episode))
    for j in range(i + 1, len(episode))
}
assert ("REVOKE", "ACT") not in within_episode_pairs

# Fault-free negative control contains no REVOKE event and is accepted by the
# declared effect oracle.
negative_control = ((1, 1, 1), ("OBSERVE", "ACT", "RELEASE"))
def effect_fails(context, history):
    return context[:2] == (1, 1) and any(
        history[i:i + 2] == ("REVOKE", "ACT")
        for i in range(len(history) - 1))
assert not effect_fails(*negative_control)
print("PASS_METHOD_SCOPED: 16 legal episodes; mixed suite 4; 4/4 joint obligations; controls and reset boundary pass")
