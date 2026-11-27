"""Classify already-verified discrete samples; this is not an evidence verifier.

No result here establishes continuous trajectory, player floor or map completion.
The caller MUST independently verify sealed raw data, inputs and retirement first.
"""
import math

STAGES=('reverse-cross','east-turn-1','east-turn-2','east-turn-3','east-advance-1','east-advance-2')
SCOPED_RULES={'schema':'map01-east-return-endpoint-rules-v1','west_x_inclusive_min':600,'west_x_exclusive_max':688,
              'west_angle_inclusive':[170,190],'west_door_gap_positive':True,'corridor_y_inclusive':[-224,-96],
              'east_x_inclusive':[752,900],'east_angle_max_circular_degrees':15,'sampled_east_boundary_max':900,
              'health_exact':100,'death_count_exact':0,'player_floor_status':'unmeasured','continuous_path_proven':False}


def classify_endpoint(samples):
    base={'player_floor_status':'unmeasured','continuous_path_proven':False}
    def result(disposition,reason):
        return dict(base,disposition=disposition,reason=reason)
    if type(samples) is not list or len(samples)!=len(STAGES):
        return result('HOLD','required samples missing')
    for stage,row in zip(STAGES,samples):
        if type(row) is not dict or row.get('stage')!=stage or row.get('status')!='observed':
            return result('HOLD','sample identity or status differs')
        for name in ('position_x','position_y','angle','health','death_count','gap'):
            value=row.get(name)
            if type(value) not in (int,float) or not math.isfinite(value):
                return result('HOLD','sample value unavailable')
        if (not 0<=row['angle']<=360 or row['health']!=100 or row['death_count']!=0
                or row.get('physical_neutral_before_after') is not True
                or type(row.get('last_action')) is not list or len(row['last_action'])!=9
                or any(type(value) not in (int,float) or value!=0 for value in row['last_action'])):
            return result('HOLD','player or neutral status unverified')
        if not -224<=row['position_y']<=-96:
            return result('HOLD','sampled corridor boundary exceeded')
    west=samples[0]
    if not (600<=west['position_x']<688 and 170<=west['angle']<=190 and west['gap']>0):
        return result('HOLD','west precondition unqualified')
    if any(row['position_x']>900 for row in samples[1:]):
        return result('HOLD','sampled east boundary exceeded')
    end=samples[-1];angle_distance=min(end['angle'],360-end['angle'])
    if 752<=end['position_x']<=900 and angle_distance<=15:
        return result('ENDPOINT_OBSERVED','qualified discrete endpoints')
    return result('MISS','endpoint short of target or facing differs')
