"""Do not infer a successful map exit from elapsed controller wall time.

Pure evaluator-only classifier. A provider timeout/death is terminal failure;
a finished/alive/non-timeout result alone is not independently verified success.
A matching trusted map-transition receipt would be needed to certify MAP_EXIT.
"""
from __future__ import annotations


def classify(*, episode_finished: bool, player_dead: bool,
             timeout_reached: bool, transition_verified: bool = False) -> dict:
    flags=(episode_finished,player_dead,timeout_reached,transition_verified)
    if any(type(x) is not bool for x in flags):
        raise TypeError('exact boolean provider flags required')
    if not episode_finished and (player_dead or timeout_reached or transition_verified):
        raise ValueError('terminal flag on an unfinished single-player episode')
    if transition_verified and (player_dead or timeout_reached):
        raise ValueError('conflicting verified success and failure evidence')
    if not episode_finished:
        cause,success='RUNNING',False
    elif player_dead and timeout_reached:
        cause,success='DEAD_AND_TIMEOUT',False
    elif player_dead:
        cause,success='DEAD',False
    elif timeout_reached:
        cause,success='TIMEOUT',False
    elif transition_verified:
        cause,success='MAP_EXIT',True
    else:
        cause,success='ENDED_CAUSE_UNVERIFIED',None
    return {'schema':'terminal-cause-v1','cause':cause,'map_exit':success,
            'controller_visible':False,'grants_input_authority':False}
