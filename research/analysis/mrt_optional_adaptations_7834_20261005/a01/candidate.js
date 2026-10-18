(input) => {
  const paths = [{a1:0,a2:null,p:0.5},{a1:1,a2:0,p:0.25},{a1:1,a2:1,p:0.25}];
  const rows = [];
  for (let own=0; own<2; own++) for (const p0 of paths) for (const p1 of paths) {
    const joint = p0.p*p1.p;
    const ownPath = own===0 ? p0 : p1;
    const otherPath = own===0 ? p1 : p0;
    const u = own;
    rows.push(makeRow(own,1,0,ownPath.a1, joint, u));
    if (ownPath.a1===1) rows.push(makeRow(own,2,1,ownPath.a2, joint, u));
  }
  function makeRow(session,step,previous,assigned,weight,u) {
    const executed = assigned===u;
    const proximal = 2*u+previous+(executed ? 2+2*u : 0);
    return {session,step,previous,assigned,propensity:0.5,eligible:true,eligibility_stage:"pre",executed,proximal,distal:10-2*assigned,weight};
  }
  function ipw(field) {
    let n=0,d=0;
    for (const r of rows) { n += r.weight*(r.assigned*r[field]/r.propensity-(1-r.assigned)*r[field]/(1-r.propensity)); d+=r.weight; }
    return n/d;
  }
  let executed1=0,weight1=0,executed0=0,weight0=0;
  for (const r of rows) if (r.executed) {
    if (r.assigned===1) {executed1+=r.weight*r.proximal;weight1+=r.weight;}
    else {executed0+=r.weight*r.proximal;weight0+=r.weight;}
  }
  const gates={};
  for (const c of input.controls) {
    const badProp=c.propensities.some(p=>p<=0||p>=1);
    gates[c.id]=(badProp||c.missing_window||c.eligibility_stage!=="pre"||c.interference)?"NONIDENTIFIABLE":"IDENTIFIABLE";
  }
  return {allocation:input.allocation,rows,eligible_weight:rows.reduce((a,r)=>a+r.weight,0),
    proximal_assignment_effect:ipw("proximal"),distal_assignment_effect:ipw("distal"),
    executed_only_contrast:executed1/weight1-executed0/weight0,
    task_success_claim:false,eligibility_stage_all_pre:rows.every(r=>r.eligibility_stage==="pre"),gates};
}