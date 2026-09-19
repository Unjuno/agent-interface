"""Read-only road/owner preservation score, fixed before guarded pilot runs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'openttd_oracle'))
from score import score as road_score

CONTRACT={'target':[678,679,680],'forbidden':[742,743,744],'owner':0}
GUARD=[y*64+x for y in range(8,14) for x in range(36,43)]

def indexed(observation):
    guard=observation['guard']
    if len(guard)!=len(GUARD) or {t['id'] for t in guard}!=set(GUARD):raise ValueError('exact guard neighborhood required')
    if any(type(t['id']) is not int or type(t['road']) is not bool or type(t['owner']) is not int for t in guard):raise ValueError('invalid guard types')
    result={t['id']:{'road':t['road'],'owner':t['owner']} for t in guard}
    for tile in observation['tiles']:
        if result[tile['id']]!={'road':tile['road'],'owner':tile['owner']}:raise ValueError('contradictory overlapping tile records')
    return result

def score(observation,baseline):
    old=road_score(observation,CONTRACT);before=indexed(baseline);after=indexed(observation)
    changed=[t for t in GUARD if t not in CONTRACT['target'] and before[t]!=after[t]]
    checks={**old['checks'],'surrounding_road_owner_unchanged':not changed}
    return {'success':all(checks.values()),'checks':checks,'changed_surrounding_tiles':changed,'legacy_success':old['success']}
