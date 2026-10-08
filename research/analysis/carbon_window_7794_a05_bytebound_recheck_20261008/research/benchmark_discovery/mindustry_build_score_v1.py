"""Separate original placement baseline from post-control delivery baseline."""
from mindustry_flow_score_v1 import score as placement_score

def score(initial, delivery_before, after, plan):
    base=placement_score(initial,after,plan)
    if base['status']=='UNKNOWN':return base
    try:
        if delivery_before['paused'] is not True or delivery_before['task_success'] is not None:
            raise ValueError('invalid delivery baseline')
        if delivery_before['player_dead'] is not False or delivery_before['unit']['plans']!=0:
            raise ValueError('delivery began without idle live unit')
        if type(delivery_before['copper']) is not int or delivery_before['copper']<0:
            raise ValueError('invalid delivery copper')
        ticks=after['tick']-delivery_before['tick']
        if ticks<plan['simulation_ticks_min']:raise ValueError('delivery window too short')
        stable=delivery_before['tiles']==after['tiles']
        delta=after['copper']-delivery_before['copper']
        satisfied=(not base['wrong_targets'] and not base['collateral_tiles'] and
            base['source_config_preserved'] and base['core_location_preserved'] and stable and
            delta>=plan['minimum_copper_delta'])
        return {**base,'status':'VERIFIED' if satisfied else 'CONTRADICTED','contract_satisfied':satisfied,
                'initial_to_final_copper_net':base['copper_delta'],'copper_delta':delta,
                'delivery_observed':delta>=plan['minimum_copper_delta'],'delivery_ticks':ticks,
                'delivery_layout_unchanged':stable,'scope':'development six-conveyor contract; no global causal guarantee'}
    except (KeyError,TypeError,ValueError) as exc:
        return {'status':'UNKNOWN','contract_satisfied':None,'reason':str(exc)}
