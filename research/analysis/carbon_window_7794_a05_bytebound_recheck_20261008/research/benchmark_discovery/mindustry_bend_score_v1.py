"""Per-tile direction checks for a declared bent route calibration."""
import math
from mindustry_flow_score_v1 import score as placement


def score(before,after,plan):
    try:
        minimum=plan['simulation_ticks_min']
        if type(minimum) not in (int,float) or not math.isfinite(minimum) or minimum<=0:
            raise ValueError('invalid simulation window')
        goal=plan['minimum_copper_delta']
        if type(goal) is not int or goal<=0:raise ValueError('invalid copper goal')
        route=plan['rotations'];directions={}
        for row in route:
            if len(row)!=3 or any(type(v) is not int for v in row) or not 0<=row[2]<=3:
                raise ValueError('invalid route direction')
            key=tuple(row[:2])
            if key in directions:raise ValueError('duplicate route coordinate')
            directions[key]=row[2]
        if set(directions)!={tuple(t) for t in plan['targets']}:
            raise ValueError('route and target coverage differ')
        result=placement(before,after,plan)
        if result['status']=='UNKNOWN':return result
        tiles={(t['x'],t['y']):t for t in after['tiles']}
        wrong=[list(k) for k,v in directions.items() if tiles[k]['rotation']!=v]
        satisfied=result['contract_satisfied'] and not wrong
        return dict(result,wrong_directions=wrong,status='VERIFIED' if satisfied else 'CONTRADICTED',
                    contract_satisfied=satisfied,scope='declared bent-route calibration; no controller construction or global causal proof')
    except (KeyError,TypeError,ValueError,IndexError) as error:
        return dict(status='UNKNOWN',contract_satisfied=None,reason=str(error))
