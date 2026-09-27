"""Combine per-tile bent-route evidence with separate delivery-window validation."""
from mindustry_build_score_v2 import score as delivery_score
from mindustry_bend_score_v1 import score as direction_score


def score(initial, delivery_before, after, plan):
    delivery=delivery_score(initial,delivery_before,after,plan)
    if delivery['status']=='UNKNOWN':return delivery
    direction=direction_score(initial,after,plan)
    if direction['status']=='UNKNOWN':return direction
    satisfied=delivery['contract_satisfied'] and not direction['wrong_directions']
    return dict(delivery,wrong_directions=direction['wrong_directions'],
        status='VERIFIED' if satisfied else 'CONTRADICTED',contract_satisfied=satisfied,
        scope='Eight-tile bent-route construction with separate post-control delivery; local final-state guard only')
