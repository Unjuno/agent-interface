(input,report) => {
  const close=(a,b)=>Number.isFinite(a)&&Math.abs(a-b)<1e-12;
  const assignP=(prior,arm)=>{
    if(prior===0)return [0.5,0.25,0.25][arm];
    if(prior===1)return [0.25,0.5,0.25][arm];
    return [0.2,0.3,0.5][arm];
  };
  const y=(type,prior,arm)=>{
    let carry=0;
    if(prior===1)carry=0.5;else if(prior===2)carry=1;
    let effect=0;
    if(arm===1)effect=2+type+(prior===2?0.5:0);
    else if(arm===2)effect=-1+2*type+(prior===1?1:0);
    return 1+2*type+prior+carry+effect;
  };
  const observe=[{v:true,p:0.8},{v:false,p:0.2}],paths=[];
  for(let type=0;type<2;type++){
    const list=[],pFirst=[0.5,0.25,0.25];
    for(let first=0;first<3;first++)for(const cFirst of observe){
      const row1={step:1,previous:0,assigned:first,probabilities:pFirst,observation_probability:0.8,
        observed:cFirst.v,eligible:true,eligibility_stage:"pre",executed:first!==((type+1)%3),
        proximal:cFirst.v?y(type,0,first):null};
      if(first===0){list.push({steps:[row1],p:pFirst[first]*cFirst.p,a1:first,a2:null});continue;}
      for(let second=0;second<3;second++)for(const cSecond of observe){
        const pSecond=[0.25,0.5,0.25][second]===undefined?0:assignP(first,second);
        const row2={step:2,previous:first,assigned:second,probabilities:(first===1?[0.25,0.5,0.25]:[0.2,0.3,0.5]),
          observation_probability:0.8,observed:cSecond.v,eligible:true,eligibility_stage:"pre",
          executed:second!==((type+first+1)%3),proximal:cSecond.v?y(type,first,second):null};
        list.push({steps:[row1,row2],p:pFirst[first]*cFirst.p*pSecond*cSecond.p,a1:first,a2:second});
      }
    }
    paths.push(list);
  }
  const expected=[];
  for(const left of paths[0])for(const right of paths[1]){
    const joint=left.p*right.p;
    for(let session=0;session<2;session++){
      const own=session===0?left:right;
      for(const s of own.steps)expected.push({session,step:s.step,previous:s.previous,assigned:s.assigned,
        assignment_probabilities:s.probabilities,propensity:s.probabilities[s.assigned],
        observation_probability:s.observation_probability,observed:s.observed,eligible:s.eligible,
        eligibility_stage:s.eligibility_stage,executed:s.executed,proximal:s.proximal,weight:joint});
    }
  }
  const key=r=>JSON.stringify([r.session,r.step,r.previous,r.assigned,r.assignment_probabilities,r.propensity,
    r.observation_probability,r.observed,r.eligible,r.eligibility_stage,r.executed,r.proximal,r.weight]);
  const multiset=rows=>{const m=new Map();for(const r of rows)m.set(key(r),(m.get(key(r))||0)+1);return m;};
  const em=multiset(expected),rm=multiset(report.rows);
  const rowsMatch=em.size===rm.size&&[...em].every(([k,v])=>rm.get(k)===v);
  const denominator=3;
  const effects={1:0,2:0};
  let observedWeight=0;
  for(const r of expected){
    if(r.observed){observedWeight+=r.weight;for(const arm of [1,2]){
      if(r.assigned===arm)effects[arm]+=r.weight*r.proximal/(r.propensity*r.observation_probability);
      if(r.assigned===0)effects[arm]-=r.weight*r.proximal/(r.propensity*r.observation_probability);
    }}
  }
  for(const arm of [1,2])effects[arm]/=denominator;
  const distal={};
  for(let type=0;type<2;type++){
    let total=0;const pFirst=[0.5,0.25,0.25];
    for(let first=0;first<3;first++){
      if(first===0) total+=pFirst[first]*(10+type-1.5*first);
      else for(let second=0;second<3;second++)total+=pFirst[first]*assignP(first,second)*(10+type-1.5*first-0.75*second);
    }
    distal[type]=total;
  }
  const executed=[0,0,0],assigned=[0,0,0];
  for(const r of expected){assigned[r.assigned]+=r.weight;if(r.executed)executed[r.assigned]+=r.weight;}
  const fractions=assigned.map((v,i)=>v?executed[i]/v:null);
  const gates={};
  for(const c of input.controls)gates[c.id]=
    (c.propensities.some(p=>p<=0||p>=1)||c.observation_probability<=0||c.observation_probability>1||
     c.missing_window||c.eligibility_stage!=="pre"||c.interference||c.carryover_beyond_identified_horizon)
      ?"NONIDENTIFIABLE":"IDENTIFIABLE";
  const obsRate=observedWeight/denominator;
  const vectorClose=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>close(v,b[i]));
  const mapClose=(a,b)=>a&&b&&Object.keys(a).length===Object.keys(b).length&&Object.keys(b).every(k=>close(a[k],b[k]));
  const rowSetMatches=rows=>{const m=multiset(rows);return em.size===m.size&&[...em].every(([k,v])=>m.get(k)===v);};
  const candidateValid=x=>x.allocation===input.allocation&&x.rows.length===expected.length&&rowSetMatches(x.rows)&&
    close(x.eligible_weight,denominator)&&close(x.observation_rate,obsRate)&&
    close(x.proximal_effect_arm1_vs0,effects[1])&&close(x.proximal_effect_arm2_vs0,effects[2])&&
    vectorClose(x.executed_fraction_by_arm,fractions)&&
    mapClose(x.distal_policy_outcome_by_type,distal)&&
    x.task_success_claim===false&&x.eligibility_stage_all_pre===true&&JSON.stringify(x.gates)===JSON.stringify(gates);
  const base=candidateValid(report);
  const checks=[],mutate=(id,fn)=>{const x=JSON.parse(JSON.stringify(report));fn(x);checks.push({id,rejected:!candidateValid(x)});};
  mutate("wrong_allocation",x=>x.allocation+="x");
  mutate("drop_row",x=>x.rows.pop());
  mutate("wrong_assignment_probability",x=>x.rows[0].assignment_probabilities[0]+=0.1);
  mutate("wrong_propensity",x=>x.rows[0].propensity+=0.1);
  mutate("wrong_censor_probability",x=>x.rows[0].observation_probability=0.9);
  mutate("censored_as_observed",x=>{const r=x.rows.find(r=>!r.observed);r.observed=true;});
  mutate("wrong_arm1_effect",x=>x.proximal_effect_arm1_vs0+=1);
  mutate("wrong_arm2_effect",x=>x.proximal_effect_arm2_vs0+=1);
  mutate("wrong_observation_rate",x=>x.observation_rate=1);
  mutate("wrong_distal",x=>x.distal_policy_outcome_by_type[0]+=1);
  mutate("proximal_as_task_success",x=>x.task_success_claim=true);
  mutate("zero_assignment_support_gate",x=>x.gates.zero_arm_support="IDENTIFIABLE");
  mutate("zero_observation_support_gate",x=>x.gates.zero_observation_support="IDENTIFIABLE");
  mutate("missing_window_gate",x=>x.gates.missing_window_unknown="IDENTIFIABLE");
  mutate("post_treatment_eligibility_gate",x=>x.gates.post_treatment_eligibility="IDENTIFIABLE");
  mutate("session_interference_gate",x=>x.gates.session_interference="IDENTIFIABLE");
  mutate("unbounded_carryover_gate",x=>x.gates.unbounded_carryover="IDENTIFIABLE");
  return {allocation:input.allocation,base_audit:base,expected_rows:expected.length,observed_rows:report.rows.length,
    eligible_weight:denominator,observation_rate:obsRate,oracle_arm1_vs0:effects[1],oracle_arm2_vs0:effects[2],
    distal_oracle_by_type:distal,mutation_count:checks.length,mutations:checks};
}