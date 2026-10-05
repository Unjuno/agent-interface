(input) => {
  const armProbabilities = previous => {
    if (previous === 0) return [0.5, 0.25, 0.25];
    if (previous === 1) return [0.25, 0.5, 0.25];
    return [0.2, 0.3, 0.5];
  };
  const censor = [{observed:true,p:0.8},{observed:false,p:0.2}];
  const score = (u, previous, assigned) => {
    const carry = previous === 1 ? 0.5 : previous === 2 ? 1 : 0;
    const direct = assigned === 0 ? 0 :
      assigned === 1 ? 2 + u + (previous === 2 ? 0.5 : 0) :
      -1 + 2*u + (previous === 1 ? 1 : 0);
    return 1 + 2*u + previous + carry + direct;
  };
  const paths = u => {
    const result = [];
    const firstP = [0.5,0.25,0.25];
    for (let a1=0;a1<3;a1++) for (const c1 of censor) {
      const first = {step:1,previous:0,assigned:a1,probabilities:firstP,observation_probability:0.8,
        observed:c1.observed,eligible:true,eligibility_stage:"pre",executed:a1!==((u+1)%3),
        proximal:c1.observed?score(u,0,a1):null};
      const p1=firstP[a1]*c1.p;
      if (a1===0) { result.push({steps:[first],p:p1,a1,a2:null}); continue; }
      const secondP=armProbabilities(a1);
      for (let a2=0;a2<3;a2++) for (const c2 of censor) {
        const second={step:2,previous:a1,assigned:a2,probabilities:secondP,observation_probability:0.8,
          observed:c2.observed,eligible:true,eligibility_stage:"pre",executed:a2!==((u+a1+1)%3),
          proximal:c2.observed?score(u,a1,a2):null};
        result.push({steps:[first,second],p:p1*secondP[a2]*c2.p,a1,a2});
      }
    }
    return result;
  };
  const p0=paths(0),p1=paths(1),rows=[];
  for (const left of p0) for (const right of p1) {
    const joint=left.p*right.p;
    for (let session=0;session<2;session++) {
      const own=session===0?left:right, u=session;
      for (const s of own.steps) rows.push({session,step:s.step,previous:s.previous,assigned:s.assigned,
        assignment_probabilities:s.probabilities,propensity:s.probabilities[s.assigned],
        observation_probability:s.observation_probability,observed:s.observed,eligible:s.eligible,
        eligibility_stage:s.eligibility_stage,executed:s.executed,proximal:s.proximal,weight:joint});
    }
  }
  const eligibleWeight=rows.reduce((n,r)=>n+r.weight,0);
  const observedWeight=rows.reduce((n,r)=>n+(r.observed?r.weight:0),0);
  const effect=arm=>{
    let numerator=0;
    for (const r of rows) {
      if (!r.observed) continue;
      const y=r.proximal/(r.propensity*r.observation_probability);
      if (r.assigned===arm) numerator+=r.weight*y;
      if (r.assigned===0) numerator-=r.weight*y;
    }
    return numerator/eligibleWeight;
  };
  const assignedWeight=[0,0,0],executedWeight=[0,0,0];
  for (const r of rows) {assignedWeight[r.assigned]+=r.weight;if(r.executed)executedWeight[r.assigned]+=r.weight;}
  const distalByType={};
  for (const u of [0,1]) {
    let total=0;
    for (const path of paths(u)) total+=path.p*(10+u-1.5*path.a1-(path.a2===null?0:0.75*path.a2));
    distalByType[u]=total;
  }
  const gates={};
  for (const control of input.controls) {
    const unsupported=control.propensities.some(p=>p<=0||p>=1)||control.observation_probability<=0||control.observation_probability>1;
    const invalid=unsupported||control.missing_window||control.eligibility_stage!=="pre"||
      control.interference||control.carryover_beyond_identified_horizon;
    gates[control.id]=invalid?"NONIDENTIFIABLE":"IDENTIFIABLE";
  }
  return {allocation:input.allocation,rows,eligible_weight:eligibleWeight,
    observation_rate:observedWeight/eligibleWeight,
    proximal_effect_arm1_vs0:effect(1),proximal_effect_arm2_vs0:effect(2),
    executed_fraction_by_arm:assignedWeight.map((w,i)=>w?executedWeight[i]/w:null),
    distal_policy_outcome_by_type:distalByType,
    task_success_claim:false,eligibility_stage_all_pre:rows.every(r=>r.eligibility_stage==="pre"),gates};
}