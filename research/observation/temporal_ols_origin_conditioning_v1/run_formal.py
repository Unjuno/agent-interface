import json, pathlib, sys
from cases import formal_cases, materialize, HORIZON_NS
from predictor import predict_absolute_float_seconds, predict_origin_shifted_delta_seconds

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: run_formal.py OUT.json')
    rows=[]
    for c in formal_cases():
        ts,xs,truth=materialize(c['trace'], c['origin_ns'])
        if c['policy']=='absolute_float_seconds':
            pred=predict_absolute_float_seconds(ts,xs,HORIZON_NS)
        else:
            pred=predict_origin_shifted_delta_seconds(ts,xs,HORIZON_NS)
        rows.append({
            'case_id':c['case_id'],'trace':c['trace']['name'],'origin_ns':c['origin_ns'],'policy':c['policy'],
            'timestamps_ns':ts,'positions':xs,'horizon_ns':HORIZON_NS,'truth':truth,'prediction':pred,
            'abs_error':abs(pred-truth),
        })
    out={'task':'TEMPORAL-OLS-ORIGIN-CONDITIONING-20260917-001','formal_invocations':1,'formal_reruns':0,'rows':rows}
    pathlib.Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows)},sort_keys=True))
if __name__=='__main__': main()
