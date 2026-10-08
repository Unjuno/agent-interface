(() => {
  const NAMES=["freshness","lease","handoff","owner","capability","protocol","backend","retry","concurrent","summary"];
  const n=NAMES.length, size=1<<n;
  const decode=id=>Object.fromEntries(NAMES.map((name,i)=>[name,Number(id.toString(2).padStart(n,"0")[i])]));
  const configValid=x=>!(x.handoff===1&&x.owner===0)&&!(x.retry===1&&x.backend===0&&x.handoff===0);
  const expectedFaults=x=>{
    const out=[];
    if(x.freshness&&x.lease)out.push("STALE_WITH_EXPIRED_LEASE");
    if(x.handoff&&x.owner&&x.concurrent)out.push("LOST_HANDOFF_WITH_CONCURRENT_OWNER");
    if(x.capability&&x.protocol)out.push("CAPABILITY_BYPASS_WITH_REORDERED_PROTOCOL");
    if(x.lease&&x.backend&&x.retry)out.push("EXPIRED_LEASE_DELAYED_DUPLICATE_RETRY");
    if(x.freshness&&x.summary&&x.capability)out.push("STALE_COMPRESSED_EVIDENCE_WITH_BYPASS");
    return out;
  };
  const classify=id=>{
    const x=decode(id);
    if(!configValid(x))return {decision:"STOP_INVALID_CONFIGURATION",faults:[],effects:0};
    const faults=expectedFaults(x);
    return {decision:faults.length?"STOP_HAZARD":"SAFE_NO_EFFECT",faults,effects:0};
  };
  const all=Array.from({length:size},(_,i)=>i);
  const validIds=all.filter(id=>configValid(decode(id)));
  const choose=(m,k)=>{
    const out=[];
    const go=(s,a)=>{if(a.length===k){out.push(a.slice());return;}for(let i=s;i<=m-(k-a.length);i++){a.push(i);go(i+1,a);a.pop();}};
    go(0,[]);return out;
  };
  const key=(id,inds)=>inds.map(i=>i+":"+decode(id)[NAMES[i]]).join(",");
  const feasiblePatterns=t=>{
    const result=new Set(), inds=choose(n,t);
    for(const id of validIds)for(const c of inds)result.add(key(id,c));
    return {inds,result};
  };
  const verifyCover=(obj,t)=>{
    const {inds,result}=feasiblePatterns(t),seen=new Set();
    for(const id of obj.rows||[])for(const c of inds)seen.add(key(id,c));
    if(seen.size!==result.size||[...result].some(x=>!seen.has(x)))throw Error("incomplete "+t+"-way cover");
    if(obj.strength!==t||obj.target_patterns!==result.size||obj.covered_patterns!==result.size)throw Error("cover metadata mismatch");
  };
  const auditCore=raw=>{
    if(!raw||raw.schema!=="constrained-interaction-5330-t0-v1")throw Error("schema");
    if(raw.freeze.issue!==5330||raw.freeze.base_main!=="1a27aff369ad1f690d4df6dc1664226ecc0726bb")throw Error("freeze identity");
    if(raw.freeze.factor_count!==n||raw.freeze.assignment_count!==size||raw.freeze.valid_assignment_count!==validIds.length)throw Error("space count");
    verifyCover(raw.pairwise_design,2);verifyCover(raw.triple_design,3);
    const policyNames=["ONE_FAULT_AT_A_TIME","CONSTRAINED_PAIRWISE","CONSTRAINED_THREE_WAY","UNCONSTRAINED_RANDOM_CHAOS_FIXED_SEED_21296"];
    if(!Array.isArray(raw.policies)||raw.policies.length!==policyNames.length)throw Error("policy set");
    for(let p=0;p<policyNames.length;p++){
      const pack=raw.policies[p];if(pack.policy!==policyNames[p])throw Error("policy ordering");
      const ids=pack.rows.map(r=>r.id);if(new Set(ids).size!==ids.length)throw Error("duplicate policy row");
      for(const r of pack.rows){
        const x=decode(r.id),valid=configValid(x),c=classify(r.id);
        if(r.bits!==r.id.toString(2).padStart(n,"0")||r.valid!==valid)throw Error("row encoding/validity");
        if(r.decision!==c.decision||JSON.stringify(r.faults)!==JSON.stringify(c.faults)||r.effects!==0)throw Error("row oracle/effect");
      }
      const found=[...new Set(pack.rows.flatMap(r=>r.faults))].sort();
      if(pack.run_count!==ids.length||pack.invalid_count!==pack.rows.filter(r=>!r.valid).length||
        pack.discovery_count!==found.length||JSON.stringify(pack.hazards_discovered)!==JSON.stringify(found)||
        pack.unsafe_effect_count!==0)throw Error("policy aggregate");
    }
    const baseline=[0,...NAMES.map((_,i)=>1<<(n-1-i)).filter(id=>configValid(decode(id)))];
    if(JSON.stringify(raw.policies[0].rows.map(r=>r.id))!==JSON.stringify(baseline))throw Error("one-factor design");
    if(JSON.stringify(raw.policies[1].rows.map(r=>r.id))!==JSON.stringify(raw.pairwise_design.rows))throw Error("pair design binding");
    if(JSON.stringify(raw.policies[2].rows.map(r=>r.id))!==JSON.stringify(raw.triple_design.rows))throw Error("triple design binding");
    if(raw.policies[3].run_count!==raw.triple_design.rows.length)throw Error("random budget mismatch");
    let rng=0x5330;const next=()=>{rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;};
    const shuffled=all.slice();for(let i=shuffled.length-1;i>0;i--){const j=next()%(i+1);[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]];}
    if(JSON.stringify(raw.policies[3].rows.map(r=>r.id))!==JSON.stringify(shuffled.slice(0,raw.triple_design.rows.length)))throw Error("fixed random schedule");
    const faultCounts={};for(const id of validIds)for(const f of expectedFaults(decode(id)))faultCounts[f]=(faultCounts[f]||0)+1;
    if(JSON.stringify(Object.fromEntries(Object.entries(faultCounts).sort()))!==JSON.stringify(Object.fromEntries(Object.entries(raw.feasible_fault_assignment_counts).sort())))throw Error("fault assignment counts");
    const adaptive=raw.adaptive_strength_escalation;
    if(adaptive.policy!=="ADAPTIVE_STRENGTH_ESCALATION_T0")throw Error("adaptive label");
    const adaptiveIds=adaptive.rows.map(r=>r.id);
    if(new Set(adaptiveIds).size!==adaptiveIds.length||adaptive.run_count!==adaptiveIds.length)throw Error("adaptive duplicates/count");
    const expectedAdaptive=[], adaptiveSeen=new Set();
    for(const [stage,ids] of [["ONE_FAULT_AT_A_TIME",baseline],["PAIRWISE_ESCALATION",raw.pairwise_design.rows],["THREE_WAY_ESCALATION",raw.triple_design.rows]])
      for(const id of ids)if(!adaptiveSeen.has(id)){adaptiveSeen.add(id);expectedAdaptive.push({stage,id});}
    if(JSON.stringify(adaptive.rows.map(r=>({stage:r.stage,id:r.id})))!==JSON.stringify(expectedAdaptive))throw Error("adaptive schedule");
    const stageRank={"ONE_FAULT_AT_A_TIME":0,"PAIRWISE_ESCALATION":1,"THREE_WAY_ESCALATION":2};
    let lastStage=-1;
    for(const r of adaptive.rows){
      if(!(r.stage in stageRank)||stageRank[r.stage]<lastStage)throw Error("adaptive stage order");
      lastStage=stageRank[r.stage];
      const c=classify(r.id);
      if(r.bits!==r.id.toString(2).padStart(n,"0")||r.valid!==configValid(decode(r.id))||
        r.decision!==c.decision||JSON.stringify(r.faults)!==JSON.stringify(c.faults)||r.effects!==0)throw Error("adaptive row");
    }
    const discovered=[...new Set(adaptive.rows.flatMap(r=>r.faults))].sort();
    if(JSON.stringify(adaptive.discovered_faults)!==JSON.stringify(discovered)||adaptive.invalid_count!==0)throw Error("adaptive aggregate");
    for(const s of adaptive.shrink_probes){
      const c=classify(s.minimal_id);
      if(c.decision!=="STOP_HAZARD")throw Error("shrink is not failing");
      const trigger=decode(s.trigger_id), active=NAMES.map((name,i)=>trigger[name]?i:-1).filter(i=>i>=0);
      const feasible=[];
      for(let mask=0;mask<(1<<active.length);mask++){
        let sub=0;for(let j=0;j<active.length;j++)if((mask>>j)&1)sub|=1<<(n-1-active[j]);
        if(configValid(decode(sub)))feasible.push(sub);
      }
      const probes=s.probes||[], probeMap=new Map(probes.map(p=>[p.id,p.decision]));
      if(s.trials!==feasible.length||probeMap.size!==probes.length||
        feasible.some(id=>!probeMap.has(id)||probeMap.get(id)!==classify(id).decision)||
        probes.some(p=>!feasible.includes(p.id)))throw Error("shrink probe transcript");
      const failing=feasible.filter(id=>classify(id).decision==="STOP_HAZARD")
        .sort((x,y)=>x.toString(2).replace(/0/g,"").length-y.toString(2).replace(/0/g,"").length||x-y);
      if(s.minimal_id!==failing[0])throw Error("shrink minimum/tie break");
    }
    const mt=raw.metamorphic;
    if(mt.case_count!==36||mt.cases.length!==36||mt.passed!==36||mt.failed!==0)throw Error("metamorphic counts");
    const expectedMeta=[];for(const id of raw.pairwise_design.rows.slice(0,12))
      for(const transform of ["OPAQUE_ID_RENAME","EVIDENCE_ORDER_REVERSAL","IRRELEVANT_METADATA_ADD"])expectedMeta.push({id,transform});
    if(JSON.stringify(mt.cases.map(c=>({id:c.id,transform:c.transform})))!==JSON.stringify(expectedMeta))throw Error("metamorphic schedule");
    for(const c of mt.cases){
      const expected=classify(c.id);
      if(c.baseline!==expected.decision||c.changed!==expected.decision||c.invariant!==true)throw Error("metamorphic relation");
    }
    if(raw.safety_envelope.external_effects!==0||raw.safety_envelope.simulated_effects!==0||
      raw.safety_envelope.live_system_calls!==0||raw.safety_envelope.all_hazards_stop_before_effect!==true)throw Error("safety envelope");
    return {case_count:size,valid_assignments:validIds.length,pairwise_patterns:raw.pairwise_design.target_patterns,
      threeway_patterns:raw.triple_design.target_patterns,policies:policyNames.length,
      metamorphic_cases:mt.case_count,adaptive_runs:adaptive.run_count,errors:[]};
  };
  const audit=raw=>{
    const summary=auditCore(raw),controls=[];
    const cases=[
      ["candidate_decision",x=>{x.policies[0].rows[0].decision="STOP_HAZARD";}],
      ["missing_row",x=>{x.policies[1].rows.pop();}],
      ["invalid_row_admission",x=>{const p=x.policies[3],id=1<<(n-1-2),row=p.rows.find(r=>r.id===id)||
        {seq:p.rows.length,id,bits:id.toString(2).padStart(n,"0"),valid:true,decision:"SAFE_NO_EFFECT",faults:[],effects:0};
        row.valid=true;row.decision="SAFE_NO_EFFECT";row.faults=[];if(!p.rows.includes(row))p.rows.push(row);p.run_count=p.rows.length;}],
      ["simulated_effect",x=>{const p=x.policies.flatMap(y=>y.rows).find(r=>r.decision==="STOP_HAZARD");if(!p)throw Error("no hazard row");p.effects=1;}]
    ];
    for(const [name,mutate] of cases){
      const altered=JSON.parse(JSON.stringify(raw));mutate(altered);
      let rejected=false;try{auditCore(altered);}catch(_){rejected=true;}
      controls.push({control:name,rejected});
    }
    if(controls.some(x=>!x.rejected))throw Error("ineffective corruption control");
    return {outcome:"PASS_T0_SYNTHETIC_DESIGN",...summary,corruption_controls:controls};
  };
  return audit;
})()