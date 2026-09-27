from __future__ import annotations

BASE=dict(target_pos=1,target_neg=0,form_pos=1,form_neg=0,modal_pos=0,modal_neg=1,
          recovery_pos=0,recovery_neg=1,intent_pos=1,intent_neg=0,envelope_pos=1,envelope_neg=0,toolbar_flash=0)

def c(name,**kw):
    x=dict(BASE);x.update(kw);return {"name":name,"features":x}

CASES=[
 c("BASE_SUBMIT"),
 c("SAME_STATE_DIFFERENT_INTENT",intent_pos=0,intent_neg=1),
 c("TARGET_FALSE",target_pos=0,target_neg=1),
 c("FORM_FALSE",form_pos=0,form_neg=1),
 c("MODAL_TRUE",modal_pos=1,modal_neg=0),
 c("RECOVERY_TRUE",recovery_pos=1,recovery_neg=0),
 c("OUT_OF_ENVELOPE",envelope_pos=0,envelope_neg=1),
 c("IRRELEVANT_TOOLBAR",toolbar_flash=1),
 c("MISSING_TARGET",target_pos=0,target_neg=0),
 c("CONFLICT_TARGET",target_pos=1,target_neg=1),
 c("MISSING_FORM",form_pos=0,form_neg=0),
 c("CONFLICT_MODAL",modal_pos=1,modal_neg=1),
 c("MISSING_RECOVERY",recovery_pos=0,recovery_neg=0),
 c("CONFLICT_INTENT",intent_pos=1,intent_neg=1),
 c("MISSING_ENVELOPE",envelope_pos=0,envelope_neg=0),
 c("TARGET_FALSE_IRRELEVANT",target_pos=0,target_neg=1,toolbar_flash=1),
 c("FORM_FALSE_RECOVERY_TRUE",form_pos=0,form_neg=1,recovery_pos=1,recovery_neg=0),
 c("MODAL_TRUE_TARGET_FALSE",modal_pos=1,modal_neg=0,target_pos=0,target_neg=1),
 c("ENVELOPE_FALSE_MODAL_TRUE",envelope_pos=0,envelope_neg=1,modal_pos=1,modal_neg=0),
 c("SECOND_VALID_SUBMIT",toolbar_flash=2),
]
