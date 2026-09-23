#!/usr/bin/env python3
import json, sys

def strict_int(x):
    return isinstance(x, int) and not isinstance(x, bool)

def decide(packet):
    required = [
        'policy','scope','observation_id','expected_observation_id','epoch','expected_epoch',
        'observation_available_ns','proposal_ready_ns','decision_deadline_ns','lease_valid_until_ns',
        'freshness_budget_ns','proposal'
    ]
    if any(k not in packet for k in required):
        return {'decision':'REFUSE_MALFORMED','authority':False}
    for k in ['epoch','expected_epoch','observation_available_ns','proposal_ready_ns','decision_deadline_ns','lease_valid_until_ns','freshness_budget_ns']:
        if not strict_int(packet[k]):
            return {'decision':'REFUSE_MALFORMED','authority':False}
    if packet['scope'] != 'decision-deadline-v1':
        return {'decision':'REFUSE_SCOPE','authority':False}
    if packet['observation_id'] != packet['expected_observation_id']:
        return {'decision':'REFUSE_OBSERVATION','authority':False}
    if packet['epoch'] != packet['expected_epoch']:
        return {'decision':'REFUSE_EPOCH','authority':False}
    if packet['proposal'] != 'TURN_LEFT':
        return {'decision':'REFUSE_PROPOSAL','authority':False}
    if packet['proposal_ready_ns'] > packet['lease_valid_until_ns']:
        return {'decision':'REFUSE_LEASE','authority':False}
    if packet['proposal_ready_ns'] - packet['observation_available_ns'] > packet['freshness_budget_ns']:
        return {'decision':'REFUSE_FRESHNESS','authority':False}
    policy = packet['policy']
    if policy == 'EXISTING_CURRENTNESS_ONLY':
        return {'decision':'ADMIT','authority':False}
    if policy == 'EXPLICIT_DECISION_DEADLINE':
        if packet['proposal_ready_ns'] > packet['decision_deadline_ns']:
            return {'decision':'REFUSE_DECISION_DEADLINE','authority':False}
        return {'decision':'ADMIT','authority':False}
    return {'decision':'REFUSE_POLICY','authority':False}

def main():
    packet=json.load(sys.stdin)
    json.dump(decide(packet),sys.stdout,sort_keys=True)
    sys.stdout.write('\n')
if __name__=='__main__': main()
