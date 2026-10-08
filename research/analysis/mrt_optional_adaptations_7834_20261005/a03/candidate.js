(input) => {
  const choices=u=>{const q=u===0?0.25:0.75;return [{a1:0,a2:null,p:0.5},{a1:1,a2:0,p:0.5*(1-q)},{a1:1,a2:1,p:0.5*q}];};
  const rows=[];
  for(let own=0;own<2;own++)for(const p0 of choices(0))for(const p1 of choices(1)){
    const path=own===0?p0:p1,weight=p0.p*p1.p,u=own;
    rows.push(row(own,1,0,path.a1,weight,u,0.5));
    if(path.a1===1)rows.push(row(own,2,1,path.a2,weight,u,u===0?0.25:0.75));
  }
  function row(session,step,previous,assigned,weight,u,propensity){
    const executed=assigned===u,proximal=2*u+previous+(executed?2+2*u+2*previous:0);
    return {session,step,previous,assigned,propensity,eligible:true,eligibility_stage:"pre",executed,proximal,distal:10-2*assigned,weight};
  }
  const ipw=field=>{let n=0,d=0;for(const r of rows){n+=r.weight*(r.assigned*r[field]/r.propensity-(1-r.assigned)*r[field]/(1-r.propensity));d+=r.weight;}return n/d;};
  let all1=0,all1w=0,all0=0,all0w=0,ex1=0,ex1w=0,ex0=0,ex0w=0;
  for(const r of rows){if(r.assigned){all1+=r.weight*r.proximal;all1w+=r.weight;}else{all0+=r.weight*r.proximal;all0w+=r.weight;}if(r.executed){if(r.assigned){ex1+=r.weight*r.proximal;ex1w+=r.weight;}else{ex0+=r.weight*r.proximal;ex0w+=r.weight;}}}
  const gates={};for(const c of input.controls)gates[c.id]=(c.propensities.some(p=>p<=0||p>=1)||c.missing_window||c.eligibility_stage!=="pre"||c.interference)?"NONIDENTIFIABLE":"IDENTIFIABLE";
  return {allocation:input.allocation,rows,eligible_weight:rows.reduce((n,r)=>n+r.weight,0),
    proximal_assignment_effect:ipw("proximal"),distal_assignment_effect:ipw("distal"),
    no_carryover_unweighted_contrast:all1/all1w-all0/all0w,
    no_history_propensity_weighted_effect:ipw("proximal"),
    executed_only_contrast:ex1/ex1w-ex0/ex0w,
    task_success_claim:false,eligibility_stage_all_pre:rows.every(r=>r.eligibility_stage==="pre"),gates};
}