(input,report) => {
  const close=(a,b)=>Number.isFinite(a)&&Math.abs(a-b)<1e-12;
  const probability=(u,a1,a2)=>{const q=u===0?0.25:0.75;return a1===0?0.5:0.5*(a2===1?q:1-q);};
  const expected=[];
  for(let session=0;session<2;session++)for(let a10=0;a10<2;a10++)for(let a11=0;a11<2;a11++){
    const firstProb=0.25;
    const histories0=a10===0?[{a:null,p:1}]:[{a:0,p:0.75},{a:1,p:0.25}];
    const histories1=a11===0?[{a:null,p:1}]:[{a:0,p:0.25},{a:1,p:0.75}];
    for(const h0 of histories0)for(const h1 of histories1){
      const a1=session===0?a10:a11,a2=session===0?h0.a:h1.a,u=session;
      const weight=firstProb*h0.p*h1.p;
      const add=(step,previous,assigned,p)=>{const ran=assigned===u;expected.push({session,step,previous,assigned,propensity:p,eligible:true,eligibility_stage:"pre",executed:ran,proximal:2*u+previous+(ran?2+2*u+2*previous:0),distal:10-2*assigned,weight});};
      add(1,0,a1,0.5);if(a1===1)add(2,1,a2,u===0?0.25:0.75);
    }
  }
  const key=x=>JSON.stringify([x.session,x.step,x.previous,x.assigned,x.propensity,x.eligible,x.eligibility_stage,x.executed,x.proximal,x.distal,x.weight]);
  const multiset=a=>{const m=new Map();for(const x of a)m.set(key(x),(m.get(key(x))||0)+1);return m;};
  const em=multiset(expected),rm=multiset(report.rows),rowMatch=em.size===rm.size&&[...em].every(([k,n])=>rm.get(k)===n);
  let proxNum=0,distNum=0,den=0,na1=0,nw1=0,na0=0,nw0=0,ex1=0,exw1=0,ex0=0,exw0=0;
  for(let u=0;u<2;u++)for(const ctx of [{prev:0,w:1},{prev:1,w:0.5}]){
    const y0=2*u+ctx.prev+(u===0?2+2*ctx.prev:0);
    const y1=2*u+ctx.prev+(u===1?2+2*u+2*ctx.prev:0);
    proxNum+=ctx.w*(y1-y0);distNum+=ctx.w*(-2);den+=ctx.w;
  }
  for(const r of expected){if(r.assigned){na1+=r.weight*r.proximal;nw1+=r.weight;}else{na0+=r.weight*r.proximal;nw0+=r.weight;}if(r.executed){if(r.assigned){ex1+=r.weight*r.proximal;exw1+=r.weight;}else{ex0+=r.weight*r.proximal;exw0+=r.weight;}}}
  const oracle=proxNum/den,distal=distNum/den,naive=na1/nw1-na0/nw0,executed=ex1/exw1-ex0/exw0;
  const controls={};for(const c of input.controls)controls[c.id]=(c.propensities.some(p=>p<=0||p>=1)||c.missing_window||c.eligibility_stage!=="pre"||c.interference)?"NONIDENTIFIABLE":"IDENTIFIABLE";
  const base=report.allocation===input.allocation&&rowMatch&&close(report.eligible_weight,3)&&close(report.proximal_assignment_effect,oracle)&&close(report.distal_assignment_effect,distal)&&close(report.no_carryover_unweighted_contrast,naive)&&close(report.no_history_propensity_weighted_effect,oracle)&&close(report.executed_only_contrast,executed)&&Math.abs(executed-oracle)>1&&report.task_success_claim===false&&report.eligibility_stage_all_pre===true&&JSON.stringify(report.gates)===JSON.stringify(controls);
  const checks=[];
  const candidateValid=x=>x.allocation===input.allocation&&x.rows.length===expected.length&&rowMatchMut(x.rows)&&close(x.eligible_weight,3)&&close(x.proximal_assignment_effect,oracle)&&close(x.distal_assignment_effect,distal)&&close(x.no_carryover_unweighted_contrast,naive)&&close(x.no_history_propensity_weighted_effect,oracle)&&close(x.executed_only_contrast,executed)&&x.task_success_claim===false&&x.eligibility_stage_all_pre===true&&JSON.stringify(x.gates)===JSON.stringify(controls);
  function rowMatchMut(rows){const m=multiset(rows);return em.size===m.size&&[...em].every(([k,n])=>m.get(k)===n);}
  const mutate=(id,f)=>{const x=JSON.parse(JSON.stringify(report));f(x);checks.push({id,rejected:!candidateValid(x)});};
  mutate("wrong_allocation",x=>x.allocation+="x");
  mutate("drop_row",x=>x.rows.pop());
  mutate("wrong_propensity",x=>x.rows[0].propensity=0.7);
  mutate("wrong_proximal",x=>x.proximal_assignment_effect+=1);
  mutate("wrong_distal",x=>x.distal_assignment_effect+=1);
  mutate("claim_task_success_from_proximal",x=>x.task_success_claim=true);
  mutate("post_treatment_eligibility",x=>x.eligibility_stage_all_pre=false);
  mutate("wrong_no_carryover_contrast",x=>x.no_carryover_unweighted_contrast=oracle);
  mutate("zero_support_gate",x=>x.gates.zero_propensity="IDENTIFIABLE");
  mutate("missing_window_gate",x=>x.gates.missing_window="IDENTIFIABLE");
  mutate("interference_gate",x=>x.gates.session_interference="IDENTIFIABLE");
  return {allocation:input.allocation,base_audit:base,oracle_proximal:oracle,oracle_distal:distal,no_carryover_unweighted:naive,no_history_propensity_weighted:oracle,executed_only:executed,expected_rows:expected.length,observed_rows:report.rows.length,mutation_count:checks.length,mutations:checks};
}