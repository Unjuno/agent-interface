import json
from oracle import BoundCertificate, certify_bound
def run():
    cases=[(BoundCertificate(10.0,"timeout-policy:v1",True),("TRUSTED_BOUND",10.0)),(BoundCertificate(10.0,None,True),("UNKNOWN_BOUND",None)),(BoundCertificate(10.0,"telemetry:unreviewed",False),("UNKNOWN_BOUND",None)),(BoundCertificate(float("nan"),"timeout-policy:v1",True),("INVALID_BOUND",None))]
    for c,e in cases:
        a=certify_bound(c); assert a==e,(c,a,e)
    print(json.dumps({"status":"PASS_DWELL_BOUND_PROVENANCE_ORACLE_SCOPED","cases":len(cases),"external_calls":0},sort_keys=True))
if __name__=="__main__": run()
