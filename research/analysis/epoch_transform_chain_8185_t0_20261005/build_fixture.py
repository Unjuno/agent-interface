"""Construction-only fixture authoring; never invoked by candidate/auditor formal commands."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
I=[[1,0,0],[0,1,0]]
def edge(i,s,t,srcu,dstu,epoch,M,res=0,kind='affine'):
 return {'edge_id':i,'source':s,'target':t,'source_units':srcu,'target_units':dstu,'epoch':epoch,'matrix':M,'residual':res,'kind':kind}
def rec(cid,edges,**kw):
 r={'case_id':cid,'source_frame':'presented','input_frame':'backend','observation_epoch':1,'source_units':'px','input_units':'px','point':[10.0,10.0],'target_id':'button-save','target_box_target_id':'button-save','target_box':[18.0,18.0,22.0,22.0],'forbidden_boxes':[[80,80,90,90]],'edges':edges}
 r.update(kw);return r
# All matrices map the presented point (10,10) to the intended backend target.
trans=edge('translate','presented','backend','px','px',1,[[1,0,10],[0,1,10]])
scale=edge('dpi150','presented','backend','px','device_px',1,[[1.5,0,3],[0,1.5,3]])
crop=edge('crop','presented','capture','px','px',1,[[1,0,4],[0,1,2]])
client=edge('client','capture','client','px','px',1,[[1,0,3],[0,1,5]])
monitor=edge('monitor','client','backend','px','device_px',1,[[1.5,0,0],[0,1.5,0]])
win=edge('window','capture','client','px','px',1,[[1,0,3],[0,1,5]])
# Point 10,10 -> capture14,12 -> client17,17 -> backend25.5,25.5.
cases=[]; truth=[]
def add(r,oracle_class='valid_affine',truth_id='button-save',oracle_box=None):
 cases.append(r);truth.append({'case_id':r['case_id'],'class':oracle_class,'target_id':truth_id,'target_box':oracle_box or r['target_box'],'expected_input_frame':'backend','expected_input_units':r['input_units'],'expected_point':{'stable_identity':[10,10],'window_translation':[20,20],'uniform_dpi_update':[18,18],'mixed_monitor_update':[25.5,25.5],'two_epoch_composition':[25.5,25.5],'composed_small_uncertainty':[18,17],'shared_uncertainty_control':[10,10],'independent_error_crosses_edge':[10,10],'uncertainty_crosses_target':[20,20],'uncertainty_hits_forbidden':[80,80]}.get(r['case_id'])})
add(rec('stable_identity',[edge('identity','presented','backend','px','px',1,I)],target_box=[9.9,9.9,10.1,10.1]),oracle_box=[9.9,9.9,10.1,10.1])
add(rec('window_translation',[trans],target_box=[19,19,21,21]),oracle_box=[19,19,21,21])
add(rec('uniform_dpi_update',[scale],input_units='device_px',target_box=[17,17,19,19]),oracle_box=[17,17,19,19])
add(rec('mixed_monitor_update',[crop,client,monitor],input_units='device_px',target_box=[24.5,24.5,26.5,26.5]),oracle_box=[24.5,24.5,26.5,26.5])
add(rec('two_epoch_composition',[crop,win,monitor],input_units='device_px',target_box=[24.5,24.5,26.5,26.5]),oracle_box=[24.5,24.5,26.5,26.5])
# Valid composed edge residual is small enough to fit wholly in the enlarged target.
add(rec('composed_small_uncertainty',[edge('a','presented','capture','px','px',1,[[1,0,4],[0,1,2]],.1),edge('b','capture','backend','px','device_px',1,[[1,0,4],[0,1,5]],.1)],input_units='device_px',target_box=[17.5,16.5,18.5,17.5]),oracle_box=[17.5,16.5,18.5,17.5])
add(rec('shared_uncertainty_control',[dict(edge('shared','presented','backend','px','px',1,I),correlation_id='common-shift',correlated_error=[.8,.8])],target_box=[9.9,9.9,10.1,10.1],target_correlated_uncertainty={'common-shift':[.8,.8]}),oracle_box=[9,9,11,11])
add(rec('independent_error_crosses_edge',[edge('uncertain','presented','backend','px','px',1,I,1.1)],target_box=[9.9,9.9,10.1,10.1]),oracle_box=[9.9,9.9,10.1,10.1])
add(rec('stale_epoch',[edge('old','presented','backend','px','px',0,I)]),'stale_epoch')
add(rec('missing_edge',[]),'missing_edge')
add(rec('reversed_edge',[edge('reverse','backend','presented','px','px',1,I)]),'reversed_edge')
add(rec('duplicate_edge',[edge('dup','presented','capture','px','px',1,I),edge('dup','capture','backend','px','px',1,I)]),'duplicate_edge')
add(rec('unit_mismatch',[edge('units','presented','backend','logical_px','device_px',1,I)]),'unit_mismatch')
add(rec('changed_input_dpi_context',[edge('dpi-old','presented','backend','px','device_px',1,I)],input_units='logical_px'),'changed_input_dpi_context')
add(rec('target_identity_swap',[trans],target_id='button-delete'),'target_identity_swap',truth_id='button-save')
add(rec('non_affine_reflow',[edge('reflow','presented','backend','px','px',1,I,kind='non_affine')]),'non_affine_reflow')
add(rec('uncertainty_crosses_target',[edge('border','presented','backend','px','px',1,[[1,0,10],[0,1,10]],1.1)],target_box=[19,19,21,21]),'uncertainty_boundary')
add(rec('uncertainty_hits_forbidden',[edge('forbidden','presented','backend','px','px',1,[[1,0,70],[0,1,70]],2)],target_box=[79,79,83,83],forbidden_boxes=[[81,81,84,84]]),'forbidden_region')
# Fix expected target units for each case based on final endpoint.
for r,t in zip(cases,truth):
 t['expected_input_units']=r['input_units'];t['expected_target_id']='button-save'
# Candidate input contains declared public edges/regions only; exact truth lives in separate file.
(ROOT/'candidate_input.json').write_text(json.dumps({'schema':'issue8185.candidate.input.v1','allocation':'8185-TRANSFORM-GRAPH-T0-20261005-01','cases':cases},sort_keys=True,indent=2)+'\n')
(ROOT/'oracle_truth.json').write_text(json.dumps({'schema':'issue8185.oracle.truth.v1','allocation':'8185-TRANSFORM-GRAPH-T0-20261005-01','truth':truth},sort_keys=True,indent=2)+'\n')
