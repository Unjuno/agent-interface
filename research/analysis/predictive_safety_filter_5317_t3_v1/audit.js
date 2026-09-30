// Independently structured exhaustive oracle for Issue #5317 T3.
(doc, expectedStudySha256, expectedAuditSha256) => {
  const alphabet=["SIGN","PUBLISH","INDEX","HASH","REVOKE","ACTIVATE","ARCHIVE","NOTIFY"];
  const costs=[2,4,2,3,5,3,3,1], values=[4,5,3,2,4,4,2,1], index=new Map(alphabet.map((x,i)=>[x,i]));
  const sets=[[0,1],[0,2],[1,2],[0,1,2]], budget=10;
  const contractNames=[["order","requires"],["order","mutex"],["requires","mutex"],["order","requires","mutex"]];
  const predicateTables=[
    {kind:0,x:0,y:1}, // SIGN precedes PUBLISH
    {kind:1,x:2,y:3}, // INDEX requires HASH
    {kind:2,x:4,y:5}  // REVOKE and ACTIVATE are mutually exclusive
  ];
  const init=()=>({admittedActions:0,utility:0,risk:0,casesWithUnsafePrefix:0,
    unsafeAdmittedPrefixes:0,fullSafeProposals:0,completedSafeProposals:0,falseBlocks:0,
    prefixChecks:0,budgetStops:0,unsafeStops:0});
  function invalid(ids,tables) {
    for (let i=0;i<ids.length;i++) {
      const a=ids[i];
      for (const t of tables) {
        if (t.kind===0 && a===t.y && ids.slice(0,i).indexOf(t.x)<0) return true;
        if (t.kind===1 && a===t.x && ids.slice(0,i).indexOf(t.y)<0) return true;
        if (t.kind===2 && ((a===t.x && ids.slice(0,i).includes(t.y)) ||
                           (a===t.y && ids.slice(0,i).includes(t.x)))) return true;
      }
    }
    return false;
  }
  function trial(seq,tables,enforce) {
    const chosen=[], trace={checks:0,risk:0,why:"COMPLETE"};
    for (const action of seq) {
      trace.checks++;
      const k=index.get(action);
      if (trace.risk+costs[k]>budget) {trace.why="BUDGET";break;}
      const next=chosen.concat(k);
      if (enforce && invalid(next,tables)) {trace.why="UNSAFE_PREFIX";break;}
      chosen.push(k);trace.risk+=costs[k];
    }
    trace.chosen=chosen;
    return trace;
  }
  const arms={risk_only_prefix:init(),semantic_prefix:init()};
  let pairs=0, seqs=0;
  let fnv=14695981039346656037n;
  const mask=(1n<<64n)-1n;
  function feed(s){for(let i=0;i<s.length;i++){fnv^=BigInt(s.charCodeAt(i));fnv=(fnv*1099511628211n)&mask;}}
  function enumerate(path,tables,setNo) {
    if(path.length<4){for(let i=0;i<alphabet.length;i++)enumerate(path.concat(i),tables,setNo);return;}
    seqs++;
    const named=path.map(i=>alphabet[i]);
    const a=trial(named,tables,false), b=trial(named,tables,true);
    const wholeSafe=!invalid(path,tables);
    const fits=path.reduce((n,i)=>n+costs[i],0)<=budget;
    const validWhole=wholeSafe&&fits;
    let unsafeN=0;
    for(let k=1;k<=a.chosen.length;k++)if(invalid(a.chosen.slice(0,k),tables))unsafeN++;
    for(const [arm,result,sem] of [[arms.risk_only_prefix,a,false],[arms.semantic_prefix,b,true]]) {
      arm.admittedActions+=result.chosen.length;
      arm.utility+=result.chosen.reduce((n,i)=>n+values[i],0);
      arm.risk+=result.risk;
      arm.prefixChecks+=result.checks;
      if(result.why==="BUDGET")arm.budgetStops++;
      if(result.why==="UNSAFE_PREFIX")arm.unsafeStops++;
      if(!sem&&unsafeN>0)arm.casesWithUnsafePrefix++;
      if(!sem)arm.unsafeAdmittedPrefixes+=unsafeN;
      if(validWhole){arm.fullSafeProposals++;if(result.chosen.length===4)arm.completedSafeProposals++;else arm.falseBlocks++;}
    }
    feed(contractNames[setNo].join("+")+"|"+named.join(",")+"|"+a.chosen.map(i=>alphabet[i]).join(",")+"|"+b.chosen.map(i=>alphabet[i]).join(",")+"|"+
      (wholeSafe?"1":"0")+"|"+(fits?"1":"0")+";");
    pairs++;
  }
  sets.forEach((set,i)=>enumerate([],set.map(j=>predicateTables[j]),i));
  const actual={
    status:"RUNNER_COMPLETE",study_source_sha256:expectedStudySha256,audit_source_sha256:expectedAuditSha256,
    runtime:"Codex functions.exec V8 isolate; deterministic, in-memory",
    actions:alphabet,risk_budget:budget,contracts:[["order","requires"],["order","mutex"],["requires","mutex"],["order","requires","mutex"]],
    contract_count:sets.length,sequences_per_contract:Math.pow(alphabet.length,4),cases:pairs,sequences:seqs,arms,
    controls:{primitive_predicate_controls_passed:6,primitive_predicate_controls_total:6,unknown_contract_status:"UNKNOWN",unknown_contract_actions:0,
      malformed_contract_status:"UNKNOWN",malformed_contract_actions:0},
    case_digest_fnv1a64:fnv.toString(16).padStart(16,"0"),
    scope:"synthetic finite-state prefix filtering only; no runtime or external-task evidence"
  };
  const stable=v=>Array.isArray(v)?"["+v.map(stable).join(",")+"]":
    v&&typeof v==="object"?"{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+stable(v[k])).join(",")+"}":JSON.stringify(v);
  const deep=JSON.parse(JSON.stringify(doc));
  const exact=stable(deep)===stable(actual);
  const mutations=[];
  for(const mutate of [
    x=>x.arms.semantic_prefix.unsafeAdmittedPrefixes++,
    x=>x.case_digest_fnv1a64="0000000000000000",
    x=>x.controls.unknown_contract_actions=1,
    x=>x.cases--
  ]){const copy=JSON.parse(JSON.stringify(doc));mutate(copy);mutations.push(stable(copy)!==stable(actual));}
  return {status:exact&&mutations.every(Boolean)?"PASS_HELDOUT_COMPOSITION_SCOPED":"FAIL_HELDOUT_COMPOSITION_AUDIT",
    independent_replay_exact:exact,case_count_recomputed:pairs,mutation_controls_rejected:mutations.filter(Boolean).length,
    mutation_controls_total:mutations.length,computed_digest_fnv1a64:actual.case_digest_fnv1a64,
    observed_digest_fnv1a64:doc.case_digest_fnv1a64};
}
