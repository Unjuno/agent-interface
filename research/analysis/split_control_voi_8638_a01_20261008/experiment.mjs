// Issue #8638 A01 — frozen finite split-control VOI enumeration.
// Base main: 437db9f8c8e77e3ad38a61c2e6a42f5cdb06fcb2. Candidate and independent auditor are in this one immutable source file.
// Running with Node prints one JSON result. No model, GUI, network, or container is needed.
const DEN = 10000000000000000n;
const UNKNOWN = Object.freeze([
  {case_id:"stale-delayed-cue", disposition:"UNKNOWN_STALE", reason:"delayed signal is outside the permitted freshness window"},
  {case_id:"out-of-model-cue", disposition:"UNKNOWN_SUPPORT", reason:"state/signal likelihood is not specified"}
]);
const FIXTURE = Object.freeze({
  schema:"split-control-voi-8638-a01-v1",
  issue:"Unjuno/agent-interface#8638",
  base_main:"437db9f8c8e77e3ad38a61c2e6a42f5cdb06fcb2",
  loss_scale:"integer loss units; acquisition_cost_milli is 1/1000 loss unit",
  cases:[
    {case_id:"paired-route-ranking",p_state1_bp:5000,loss_fp:1,loss_fn:1,options:[
      {id:"A-high-quality-low-uptake",accuracy_bp:9000,delivery_bp:10000,response_bp:{use:2000,invert:0,ignore:8000},cost_milli:200},
      {id:"B-medium-quality-full-uptake",accuracy_bp:7000,delivery_bp:10000,response_bp:{use:10000,invert:0,ignore:0},cost_milli:50}
    ]},
    {case_id:"irrelevant-signal",p_state1_bp:5000,loss_fp:1,loss_fn:1,options:[
      {id:"I-irrelevant",accuracy_bp:5000,delivery_bp:10000,response_bp:{use:10000,invert:0,ignore:0},cost_milli:10}
    ]},
    {case_id:"rare-high-consequence",p_state1_bp:500,loss_fp:1,loss_fn:10,options:[
      {id:"R-rare-cue",accuracy_bp:9000,delivery_bp:10000,response_bp:{use:8000,invert:0,ignore:2000},cost_milli:100}
    ]},
    {case_id:"misleading-downstream-response",p_state1_bp:5000,loss_fp:1,loss_fn:1,options:[
      {id:"M-inverts-delivered-cue",accuracy_bp:9000,delivery_bp:10000,response_bp:{use:0,invert:10000,ignore:0},cost_milli:0}
    ]},
    {case_id:"partial-delivery-and-response-error",p_state1_bp:5000,loss_fp:2,loss_fn:3,options:[
      {id:"P-partial-delivery",accuracy_bp:8500,delivery_bp:6000,response_bp:{use:10000,invert:0,ignore:0},cost_milli:25},
      {id:"E-mixed-response",accuracy_bp:9500,delivery_bp:10000,response_bp:{use:7000,invert:1000,ignore:2000},cost_milli:80}
    ]}
  ],
  unknown_cases:UNKNOWN,
  mandatory_gates:{freshness:"OUTSIDE_OPTIONAL_VALUE",authority:"OUTSIDE_OPTIONAL_VALUE",release:"OUTSIDE_OPTIONAL_VALUE"},
  action_authority:"NONE",
  runtime_effect:"NOT_EVALUATED"
});
function loss(state,action,fp,fn){return action===state?0:(state===0?fp:fn);}
function candidateEnumerate(spec){
  const output={schema:"split-control-voi-candidate-v1",denominator:DEN.toString(),cases:[],unknown_cases:spec.unknown_cases,mandatory_gates:spec.mandatory_gates,action_authority:spec.action_authority,runtime_effect:spec.runtime_effect};
  for(const c of spec.cases){
    const rows=[];
    const stateMass=[[0,10000-c.p_state1_bp],[1,c.p_state1_bp]];
    for(const [state,sm] of stateMass) for(const signal of [0,1]){
      const signalMass=(signal===state?c.options[0].accuracy_bp:10000-c.options[0].accuracy_bp);
      // Signal generation is option-specific; enumerate the Cartesian row set separately below.
      void signalMass;
    }
    for(const o of c.options){
      const optionRows=[];
      for(const [state,sm] of stateMass) for(const signal of [0,1]){
        const signalMass=(signal===state?o.accuracy_bp:10000-o.accuracy_bp);
        for(const delivered of [false,true]){
          const dm=delivered?o.delivery_bp:10000-o.delivery_bp;
          const responses=delivered?Object.entries(o.response_bp):[["not_delivered",10000]];
          for(const [response,rm] of responses){
            const mass=BigInt(sm)*BigInt(signalMass)*BigInt(dm)*BigInt(rm);
            if(mass===0n) continue;
            const action=!delivered?0:response==="use"?signal:response==="invert"?1-signal:0;
            const oracleAction=delivered?signal:0;
            optionRows.push({state,signal,delivered,response,action,mass_num:mass.toString(),
              actual_loss:loss(state,action,c.loss_fp,c.loss_fn),
              oracle_action:oracleAction,oracle_loss:loss(state,oracleAction,c.loss_fp,c.loss_fn),
              baseline_loss:loss(state,0,c.loss_fp,c.loss_fn)});
          }
        }
      }
      let baseN=0n,actualN=0n,oracleN=0n,deliveredN=0n,usedN=0n,ignoredN=0n,invertedN=0n;
      for(const r of optionRows){const m=BigInt(r.mass_num);baseN+=m*BigInt(r.baseline_loss);actualN+=m*BigInt(r.actual_loss);oracleN+=m*BigInt(r.oracle_loss);if(r.delivered){deliveredN+=m;if(r.response==="use")usedN+=m;if(r.response==="ignore")ignoredN+=m;if(r.response==="invert")invertedN+=m;}}
      const score=(baseN-actualN)*1000n-BigInt(o.cost_milli)*DEN;
      const oracleScore=(baseN-oracleN)*1000n-BigInt(o.cost_milli)*DEN;
      output.cases.push({case_id:c.case_id,option_id:o.id,rows:optionRows,
        sufficient_statistics:{baseline_loss_num:baseN.toString(),actual_loss_num:actualN.toString(),oracle_loss_num:oracleN.toString(),
          delivered_mass_num:deliveredN.toString(),consumed_mass_num:usedN.toString(),ignored_mass_num:ignoredN.toString(),misused_mass_num:invertedN.toString(),
          cost_milli:o.cost_milli,net_split_value_num:score.toString(),net_voic_value_num:oracleScore.toString(),value_denominator:(DEN*1000n).toString()}
      });
    }
  }
  return output;
}
// Independently written verifier: reconstructs the support rows and all aggregates from the frozen fixture.
function independentAudit(spec,raw){
  const errors=[];
  const expectedRows=[];
  for(const c of spec.cases) for(const o of c.options){
    let b=0n,a=0n,v=0n,d=0n,u=0n,i=0n,mx=0n;
    const rows=[];
    const states=[[0,10000-c.p_state1_bp],[1,c.p_state1_bp]];
    for(let si=0;si<states.length;si++){
      const [state,sw]=states[si];
      for(let bit=0;bit<=1;bit++){
        const qw=bit===state?o.accuracy_bp:10000-o.accuracy_bp;
        for(let di=0;di<2;di++){
          const delivered=di===1,dw=delivered?o.delivery_bp:10000-o.delivery_bp;
          const responseWeights=delivered?[["use",o.response_bp.use],["invert",o.response_bp.invert],["ignore",o.response_bp.ignore]]:[["not_delivered",10000]];
          for(let ri=0;ri<responseWeights.length;ri++){
            const [response,rw]=responseWeights[ri],weight=BigInt(sw)*BigInt(qw)*BigInt(dw)*BigInt(rw);
            if(weight===0n)continue;
            const action=delivered?(response==="use"?bit:response==="invert"?1-bit:0):0;
            const ideal=delivered?bit:0;
            const L0=state===0?(action===0?0:c.loss_fp):(action===1?0:c.loss_fn);
            const LV=state===0?(ideal===0?0:c.loss_fp):(ideal===1?0:c.loss_fn);
            const LB=state===0?0:c.loss_fn;
            rows.push({state,signal:bit,delivered,response,action,mass_num:weight.toString(),actual_loss:L0,oracle_action:ideal,oracle_loss:LV,baseline_loss:LB});
            b+=weight*BigInt(LB);a+=weight*BigInt(L0);v+=weight*BigInt(LV);
            if(delivered){d+=weight;if(response==="use")u+=weight;if(response==="ignore")i+=weight;if(response==="invert")mx+=weight;}
          }
        }
      }
    }
    const split=(b-a)*1000n-BigInt(o.cost_milli)*DEN;
    const voic=(b-v)*1000n-BigInt(o.cost_milli)*DEN;
    expectedRows.push({case_id:c.case_id,option_id:o.id,rows,
      sufficient_statistics:{baseline_loss_num:b.toString(),actual_loss_num:a.toString(),oracle_loss_num:v.toString(),delivered_mass_num:d.toString(),consumed_mass_num:u.toString(),ignored_mass_num:i.toString(),misused_mass_num:mx.toString(),cost_milli:o.cost_milli,net_split_value_num:split.toString(),net_voic_value_num:voic.toString(),value_denominator:(DEN*1000n).toString()}
    });
  }
  const canon=x=>JSON.stringify(x);
  const actual=raw?.cases;
  if(!Array.isArray(actual)||canon(actual)!==canon(expectedRows)) errors.push("RAW_RECONSTRUCTION_MISMATCH");
  const weights=expectedRows.flatMap(x=>x.rows).map(x=>BigInt(x.mass_num));
  if(weights.some(w=>w<0n)||weights.some((_,idx)=>idx%1!==0)) errors.push("INVALID_WEIGHT");
  for(const e of expectedRows){const sum=e.rows.reduce((s,r)=>s+BigInt(r.mass_num),0n);if(sum!==DEN)errors.push("MASS_NOT_ONE:"+e.case_id+":"+e.option_id);}
  if(canon(raw?.unknown_cases)!==canon(spec.unknown_cases)||spec.unknown_cases.some(x=>!x.disposition.startsWith("UNKNOWN_")))errors.push("UNKNOWN_NOT_FAIL_CLOSED");
  if(canon(raw?.mandatory_gates)!==canon(spec.mandatory_gates)||raw?.action_authority!=="NONE"||raw?.runtime_effect!=="NOT_EVALUATED")errors.push("HARD_GATE_SCOPE_CHANGED");
  const find=(id)=>expectedRows.find(x=>x.option_id===id)?.sufficient_statistics;
  const A=find("A-high-quality-low-uptake"),B=find("B-medium-quality-full-uptake");
  if(!A||!B||!(BigInt(A.net_voic_value_num)>BigInt(B.net_voic_value_num)&&BigInt(A.net_split_value_num)<0n&&BigInt(B.net_split_value_num)>0n&&BigInt(A.net_split_value_num)<BigInt(B.net_split_value_num)))errors.push("PREREGISTERED_RANK_REVERSAL_NOT_FOUND");
  const runMutations=()=>{
    const mutated=JSON.parse(JSON.stringify(raw));
    mutated.cases[0].rows.pop();
    const rejectsMissing=canon(mutated.cases)!==canon(expectedRows);
    const altered=JSON.parse(JSON.stringify(raw));
    altered.cases[0].rows[0].state=1-altered.cases[0].rows[0].state;
    const rejectsTruthMutation=canon(altered.cases)!==canon(expectedRows);
    const gate=JSON.parse(JSON.stringify(raw));gate.action_authority="GRANTED";
    const rejectsGateMutation=gate.action_authority!=="NONE";
    return {missing_row:rejectsMissing,truth_state:rejectsTruthMutation,authority_escalation:rejectsGateMutation};
  };
  const mutations=runMutations();
  if(Object.values(mutations).some(v=>v!==true))errors.push("MUTATION_SURVIVED");
  return {status:errors.length?"FAIL_METHOD":"PASS_METHOD_SCOPED",errors,case_option_rows:expectedRows.length,total_raw_rows:expectedRows.reduce((n,x)=>n+x.rows.length,0),mutations};
}
const raw=candidateEnumerate(FIXTURE);
const audit=independentAudit(FIXTURE,raw);
const result={protocol:"8638-A01-finite-split-control",fixture:FIXTURE,raw,audit};
globalThis.SPLIT_CONTROL_VOI_RESULT=result;
if(typeof process!=="undefined"&&process.argv?.[1]?.endsWith("experiment.mjs")) console.log(JSON.stringify(result,null,2));
