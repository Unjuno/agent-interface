// Issue #8909 A01 — dependency-free bounded transition-system trace audit.
// Run: node research/analysis/issue_8909_cover_diagnosability_a01_20261012/a01.mjs
"use strict";
const classes = [
  { id:"fault-A", required:"yield-left", rawCue:"red", covered:true, safe:true },
  { id:"fault-B", required:"yield-right", rawCue:"blue", covered:true, safe:true },
  { id:"fault-C", required:"continue", rawCue:"green", covered:false, safe:true },
  { id:"fault-D", required:"continue", rawCue:"amber", covered:false, safe:true },
  { id:"out-of-catalog", required:"UNKNOWN", rawCue:"unclassified", covered:true, safe:true }
];
const policies=["no-cover","protective-cover","cover-plus-sentinel"];
const horizon=2;
function candidateTrace(c,policy){
  let state={id:c.id,phase:0,safe:true}; const trace=[],safePrefixes=[state.safe];
  for(let tick=0;tick<horizon;tick++){
    const observation=tick===0
      ? (policy==="no-cover"||!c.covered ? "cue:"+c.rawCue : "cover:active")
      : (policy==="cover-plus-sentinel" ? "sentinel:"+c.id : "quiet");
    trace.push(observation);
    state={...state,phase:tick+1,safe:state.safe&&c.safe}; safePrefixes.push(state.safe);
  }
  return {id:c.id,trace,safePrefixes,response:c.required};
}
function candidateModel(){
  const rows=[]; for(const policy of policies) for(const c of classes) rows.push({policy,...candidateTrace(c,policy)}); return rows;
}
// Independent reference table/oracle; does not call candidate functions.
function oracleRow(policy,id){
  const t={
    "fault-A":{cue:"red",response:"yield-left",safe:true,cover:true},
    "fault-B":{cue:"blue",response:"yield-right",safe:true,cover:true},
    "fault-C":{cue:"green",response:"continue",safe:true,cover:false},
    "fault-D":{cue:"amber",response:"continue",safe:true,cover:false},
    "out-of-catalog":{cue:"unclassified",response:"UNKNOWN",safe:true,cover:true}
  }[id];
  if(!t) throw Error("oracle lacks state");
  const first=policy==="no-cover"||!t.cover ? "cue:"+t.cue : "cover:active";
  const second=policy==="cover-plus-sentinel" ? "sentinel:"+id : "quiet";
  return {trace:[first,second],safePrefixes:[true,t.safe,true],response:t.response};
}
function audit(rows){
  if(!Array.isArray(rows)||rows.length!==classes.length*policies.length) throw Error("incomplete closure");
  for(const p of policies) for(const c of classes){
    const r=rows.find(x=>x.policy===p&&x.id===c.id); if(!r) throw Error("missing row");
    const e=oracleRow(p,c.id);
    if(JSON.stringify(r.trace)!==JSON.stringify(e.trace)) throw Error("trace/oracle mismatch "+p+"/"+c.id);
    if(JSON.stringify(r.safePrefixes)!==JSON.stringify(e.safePrefixes)) throw Error("safety/oracle mismatch "+p+"/"+c.id);
    if(r.response!==e.response) throw Error("response/oracle mismatch "+p+"/"+c.id);
  }
  const eq=(p,a,b)=>JSON.stringify(rows.find(r=>r.policy===p&&r.id===a).trace)===JSON.stringify(rows.find(r=>r.policy===p&&r.id===b).trace);
  const checks=[
    {policy:"no-cover",pair:"fault-A|fault-B",equal:eq("no-cover","fault-A","fault-B"),incompatible:true},
    {policy:"protective-cover",pair:"fault-A|fault-B",equal:eq("protective-cover","fault-A","fault-B"),incompatible:true},
    {policy:"cover-plus-sentinel",pair:"fault-A|fault-B",equal:eq("cover-plus-sentinel","fault-A","fault-B"),incompatible:true},
    {policy:"protective-cover",pair:"fault-C|fault-D",equal:eq("protective-cover","fault-C","fault-D"),incompatible:false}
  ];
  if(checks[0].equal!==false||checks[1].equal!==true||checks[2].equal!==false||checks[3].equal!==false) throw Error("pair contrast mismatch");
  const cd=rows.filter(r=>r.policy==="protective-cover"&&(r.id==="fault-C"||r.id==="fault-D"));
  if(cd[0].response!==cd[1].response) throw Error("common-response control mismatch");
  return checks;
}
function mutation(name,mutate){
  const rows=candidateModel(); mutate(rows);
  try{audit(rows);return{name,rejected:false};}catch{return{name,rejected:true};}
}
const rows=candidateModel(), pairChecks=audit(rows);
const mutations=[
  mutation("drop-one-transition-row",r=>r.pop()),
  mutation("forge-passive-sentinel",r=>{r.find(x=>x.policy==="cover-plus-sentinel"&&x.id==="fault-B").trace[1]="sentinel:fault-A";}),
  mutation("unsafe-prefix",r=>{r.find(x=>x.policy==="protective-cover"&&x.id==="fault-A").safePrefixes[1]=false;}),
  mutation("truncate-horizon",r=>{r.find(x=>x.policy==="no-cover"&&x.id==="fault-A").trace.pop();}),
  mutation("change-out-of-catalog-response",r=>{r.find(x=>x.id==="out-of-catalog").response="yield-left";})
];
if(!mutations.every(x=>x.rejected)) throw Error("mutation escaped audit");
const result={
  status:"PASS_METHOD_SCOPED",
  model:{states:classes.map(x=>x.id),policies,horizonTicks:horizon,enumeratedTraces:rows.length},
  pairChecks,
  safety:{unsafePrefixes:rows.flatMap(x=>x.safePrefixes).filter(x=>!x).length},
  mutations,
  disposition:"MASK_WITNESS_SCOPED and RESTORATION_SCOPED within this authored model only",
  limits:["Deterministic hand-authored model; no Agent Interface runtime/GUI measured","Sentinel is assumed truthful by the frozen table; its provenance/correlation is not modeled","No prevalence, efficacy, or production safety claim","Out-of-catalog class remains UNKNOWN; no diagnosis is asserted"]
};
if(typeof process!=="undefined"&&process.stdout)process.stdout.write(JSON.stringify(result,null,2)+"\n");
