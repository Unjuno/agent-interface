# Preserved pre-formal construction defect

During construction, the first candidate implementation returned `True` whenever no invalid close was encountered, even when the parent stack remained nonempty at end-of-trace. Its output incorrectly counted 617 valid traces. This was detected by the separate oracle implementation before any source freeze/formal allocation. The defective source/output are described here; they are not formal evidence and were not used for a conclusion. Corrected candidate requires an empty terminal stack; the frozen allocation output is 51 valid balanced traces.
