(input,report) => {
  const close=(a,b)=>Number.isFinite(a)&&Math.abs(a-b)<1e-12;
  const paths=[{a1:0,a2:null,p:0.5},{a1:1,a2:0,p:0.25},{a1:1,a2:1,p:0.25}];
  const expected=[];
  for(let session=0;session<2;session++) for(const left of paths) for(const right of paths) {
    const own=session===0?left:right, other=session===0?right:left, weight=left.p*right.p, u=session;
    const add=(step,previous,assigned)=>expected.push({session,step,previous,assigned,propensity:0.5,eligible:true,eligibility_stage:"pre",executed:assigned===u,proximal:2*u+previous+(assigned===u?2+2*u:0),distal:10-2*assigned,weight});
    add(1,0,own.a1); if(own.a1===1)add(2,1,own.a2);
  }
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const rowMatch=report.rows.length===expected.length&&expected.every(e=>report.rows.some(r=>same(r,e)));
  let oracleNum=0,oracleDen=0,distalNum=0,distalDen=0;
  for(let session=0;session<2;session++) {
    const u=session;
    for(const ctx of [{step:1,previous:0,weight:1},{step:2,previous:1,weight:0.5}]) {
      for(const a of [0,1]) {
        const executed=a===u, y=2*u+ctx.previous+(executed?2+2*u:0);
        oracleNum+=ctx.weight*(a*y/0.5-(1-a)*y/0.5);
        distalNum+=ctx.weight*(a*(10-2*a)/0.5-(1-a)*(10-2*a)/0.5);
      }
      oracleDen+=2*ctx.weight;
      distalDen+=2*ctx.weight;
    }
  }
  const oracleProx=oracleNum/oracleDen,oracleDistal=distalNum/distalDen;
  let e1=0,w1=0,e0=0,w0=0;
  for(const r of expected) if(r.executed) {if(r.assigned){e1+=r.weight*r.proximal;w1+=r.weight;}else{e0+=r.weight*r.proximal;w0+=r.weight;}}
  const naive=e1/w1-e0/w0;
  const gates={};for(const c of input.controls)gates[c.id]=(c.propensities.some(p=>p<=0||p>=1)||c.missing_window||c.eligibility_stage!=="pre"||c.interference)?"NONIDENTIFIABLE":"IDENTIFIABLE";
  const base=report.allocation===input.allocation&&rowMatch&&close(report.eligible_weight,3)&&close(report.proximal_assignment_effect,oracleProx)&&close(report.distal_assignment_effect,oracleDistal)&&close(report.executed_only_contrast,naive)&&Math.abs(naive-oracleProx)>1&&report.task_success_claim===false&&report.eligibility_stage_all_pre===true&&same(report.gates,gates);
  const mutations=[];
  const mutate=(id,fn)=>{const x=JSON.parse(JSON.stringify(report));fn(x);mutations.push({id,rejected:!(x.allocation===input.allocation&&x.rows.length===expected.length&&expected.every(e=>x.rows.some(r=>same(r,e)))&&close(x.eligible_weight,3)&&close(x.proximal_assignment_effect,oracleProx)&&close(x.distal_assignment_effect,oracleDistal)&&close(x.executed_only_contrast,naive)&&x.task_success_claim===false&&x.eligibility_stage_all_pre===true&&same(x.gates,gates))});};
  mutate("wrong_allocation",x=>x.allocation+="x");
  mutate("drop_row",x=>x.rows.pop());
  mutate("wrong_proximal",x=>x.proximal_assignment_effect+=1);
  mutate("wrong_distal",x=>x.distal_assignment_effect+=1);
  mutate("claim_task_success_from_proximal",x=>x.task_success_claim=true);
  mutate("post_treatment_eligibility",x=>x.eligibility_stage_all_pre=false);
  mutate("naive_equals_itt",x=>x.executed_only_contrast=x.proximal_assignment_effect);
  mutate("zero_support_gate",x=>x.gates.zero_propensity="IDENTIFIABLE");
  mutate("missing_window_gate",x=>x.gates.missing_window="IDENTIFIABLE");
  mutate("interference_gate",x=>x.gates.session_interference="IDENTIFIABLE");
  return {allocation:input.allocation,base_audit:base,oracle_proximal:oracleProx,oracle_distal:oracleDistal,naive_executed_only:naive,expected_rows:expected.length,observed_rows:report.rows.length,mutation_count:mutations.length,mutations};
}