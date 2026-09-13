"""Score the declared narrow flow contract, never the calibration case label."""
import math

def score(before, after, plan):
    unknown = {'status':'UNKNOWN','contract_satisfied':None}
    try:
        guard=plan['guard']
        coordinates={(x,y) for y in range(guard['y_min'],guard['y_max']+1)
                     for x in range(guard['x_min'],guard['x_max']+1)}
        targets={tuple(p) for p in plan['targets']}
        if not targets or not targets <= coordinates:raise ValueError('invalid targets')
        def projection(snapshot):
            if snapshot['task_success'] is not None:raise ValueError('oracle claimed task authority')
            if type(snapshot['copper']) is not int or snapshot['copper']<0:raise ValueError('invalid copper')
            if type(snapshot['tick']) not in (int,float) or not math.isfinite(snapshot['tick']):raise ValueError('invalid tick')
            rows=snapshot['tiles']
            if not isinstance(rows,list) or len(rows)!=len(coordinates):raise ValueError('incomplete projection')
            result={}
            for t in rows:
                if set(t)!={'x','y','block','team','rotation','floor','overlay'}:raise ValueError('invalid tile fields')
                if type(t['x']) is not int or type(t['y']) is not int:raise ValueError('invalid coordinate')
                key=(t['x'],t['y'])
                if key in result or key not in coordinates:raise ValueError('duplicate or foreign coordinate')
                if not all(isinstance(t[k],str) and t[k] for k in ('block','floor','overlay')):raise ValueError('invalid tile type')
                if type(t['team']) is not int:raise ValueError('invalid team')
                if t['rotation'] is not None and (type(t['rotation']) is not int or not 0<=t['rotation']<=3):raise ValueError('invalid rotation')
                result[key]=t
            return result
        old,new=projection(before),projection(after)
        if before['paused'] is not True or after['paused'] is not True:
            return {**unknown,'reason':'window_not_closed'}
        elapsed=after['tick']-before['tick']
        if elapsed<plan['simulation_ticks_min']:
            return {**unknown,'reason':'insufficient_simulation_window'}
        if any(old[p]['block']!='air' for p in targets):raise ValueError('targets not initially empty')
        required=plan['required']
        wrong_targets=[list(p) for p in sorted(targets) if any(new[p][k]!=v for k,v in required.items())
                       or any(new[p][k]!=old[p][k] for k in ('floor','overlay'))]
        collateral=[list(p) for p in sorted(coordinates-targets) if new[p]!=old[p]]
        source_valid=before['source_item']=='copper' and after['source_item']=='copper'
        core_preserved=all(before[k]==after[k] for k in ('core_x','core_y'))
        delta=after['copper']-before['copper']
        delivered=delta>=plan['minimum_copper_delta']
        satisfied=not wrong_targets and not collateral and source_valid and core_preserved and delivered
        return {'status':'VERIFIED' if satisfied else 'CONTRADICTED','contract_satisfied':satisfied,
                'wrong_targets':wrong_targets,'collateral_tiles':collateral,'source_config_preserved':source_valid,
                'core_location_preserved':core_preserved,'copper_delta':delta,'delivery_observed':delivered,
                'simulation_ticks':elapsed,'guard_tiles':len(coordinates)}
    except (KeyError,TypeError,ValueError,IndexError) as exc:
        return {**unknown,'reason':'invalid_evidence','detail':str(exc)}
