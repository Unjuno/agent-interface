# Public metadata projection

Public turn_context payloads retain only turn_id, model and effort, the three
fields used by the pinned usage projector. Unnecessary host metadata is omitted.
Original context raw-line SHA256 and approved field list remain; token-usage
records, selected tool evidence and images are unchanged. Previously retained
normal verification describes the private originals at its original boundary.
The new publication reconstruction checks the projected records. Original-source
checks compare exact other lines and original hash plus canonical approved
context fields. Counts and images must remain identical. Historical source and
GUI experiments are not retuned; original private records remain local.
