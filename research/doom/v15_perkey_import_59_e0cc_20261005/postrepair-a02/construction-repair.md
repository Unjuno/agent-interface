# A02 construction record

The first frozen-source startup attempt stopped before route selection because the host Python lacked Pillow (`ModuleNotFoundError: No module named 'PIL'`). That first stderr is retained in `run-20261005T01/v12-perkey.stderr.txt`; no owner/session boundary was reached and no route conclusion was drawn.

No package was installed. The probe was narrowly extended to supply inert import-time `PIL`, `numpy`, `openpyxl`, Xlib, and VizDoom modules, with image capture, workbook construction, X, and game construction functions refusing calls. The measured question ends before any image, array, or workbook operation. This adaptation is included in the probe source hash before the next run. Any forbidden call remains a harness failure.
