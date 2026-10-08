"""Refuse mutation when observation or privacy policy changed after planning."""
from redaction_mutation_gate_v1 import authorize as authorize_mutation


def authorize(proposal, *, expected_text, field_target_box, save_target_box,
              private_redacted_boxes, presented_binding, current_binding):
    if proposal['kind'] == 'stop':
        return {'authorized': False, 'reason': 'planner_requested_stop'}
    proposal_binding = {name: proposal[name] for name in
                        ('observation_id', 'policy_id', 'policy_version')}
    if proposal_binding != presented_binding:
        return {'authorized': False, 'reason': 'proposal_binding_mismatch'}
    if (proposal['policy_id'], proposal['policy_version']) != (
            current_binding['policy_id'], current_binding['policy_version']):
        return {'authorized': False, 'reason': 'policy_binding_mismatch'}
    return authorize_mutation(
        proposal, expected_text=expected_text, field_target_box=field_target_box,
        save_target_box=save_target_box,
        private_redacted_boxes=private_redacted_boxes,
        observation_id=proposal['observation_id'],
        current_observation_id=current_binding['observation_id'])
