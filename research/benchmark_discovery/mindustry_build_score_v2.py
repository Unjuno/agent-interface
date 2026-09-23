"""Validate the separate delivery window before applying the frozen v1 score."""
import math
from mindustry_build_score_v1 import score as previous


def score(initial, delivery_before, after, plan):
    try:
        ticks=[]
        for snapshot in (initial,delivery_before,after):
            value=snapshot['tick']
            if type(value) not in (int,float) or not math.isfinite(value):
                raise ValueError('invalid phase tick')
            ticks.append(value)
        if not ticks[0] <= ticks[1] < ticks[2]:
            raise ValueError('phase ticks are not ordered')
        minimum=plan['simulation_ticks_min']
        if type(minimum) not in (int,float) or not math.isfinite(minimum) or minimum<=0:
            raise ValueError('invalid minimum delivery duration')
        copper=plan['minimum_copper_delta']
        if type(copper) is not int or copper<=0:
            raise ValueError('invalid minimum delivery copper')
        plans=delivery_before['unit']['plans']
        if type(plans) is not int or plans!=0:
            raise ValueError('delivery requires an integer zero pending-plan count')
    except (KeyError,TypeError,ValueError,OverflowError) as error:
        return dict(status='UNKNOWN',contract_satisfied=None,reason='invalid_delivery_measurement',detail=str(error))
    return previous(initial,delivery_before,after,plan)
