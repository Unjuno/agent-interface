"""Bounded reuse of a subject-returned role label; no implicit semantic inference."""
def apply_role(document, role_label, old_person, new_person):
    if any(type(v) is not str or not v for v in (document,role_label,old_person,new_person)):
        return {'outcome':'REFUSE','reason':'invalid_input'}
    if any('\r' in v or '\n' in v or '：' in v for v in (role_label,old_person,new_person)):
        return {'outcome':'REFUSE','reason':'invalid_line_parameter'}
    lines=document.splitlines(keepends=True)
    if not lines or any(not line.endswith('\r\n') for line in lines):
        return {'outcome':'REFUSE','reason':'unsupported_line_ending'}
    prefix=role_label+'：'
    matches=[i for i,line in enumerate(lines) if line.startswith(prefix)]
    if len(matches)!=1:
        return {'outcome':'INVALIDATED','reason':'role_not_unique','target_input_allowed':False}
    index=matches[0]
    if lines[index]!=prefix+old_person+'\r\n':
        return {'outcome':'INVALIDATED','reason':'old_person_changed','target_input_allowed':False}
    result=lines.copy();result[index]=prefix+new_person+'\r\n'
    return {'outcome':'READY','updated_text':''.join(result),'source_text':document,'changed_line':index,'next':'editor whole-body comparison, then one Save; never infer disk success from this result'}
