diff --git a/audit.py b/audit.py
--- a/audit.py
+++ b/audit.py
@@
 def validate_reader_trace_rows(rows, reader_index, pid, ready_ns):
@@
     return errors
+
+
+def validate_writer_envelope(writer_start_ns, writer_end_ns, publications):
+    if (type(writer_start_ns) is not int or type(writer_end_ns) is not int or
+            writer_start_ns <= 0 or writer_start_ns >= writer_end_ns or
+            not isinstance(publications, list) or not publications):
+        return False
+    return all(
+        isinstance(event, dict) and
+        type(event.get("start_ns")) is int and
+        type(event.get("end_ns")) is int and
+        writer_start_ns <= event["start_ns"] < event["end_ns"] <= writer_end_ns
+        for event in publications
+    )
+
+
+def validate_reader_exit(exit_ns, read_rows):
+    if type(exit_ns) is not int or exit_ns <= 0 or not isinstance(read_rows, list) or not read_rows:
+        return False
+    read_ends = [row.get("read_end_ns") for row in read_rows if isinstance(row, dict)]
+    return (
+        len(read_ends) == len(read_rows) and
+        all(type(value) is int for value in read_ends) and
+        exit_ns >= max(read_ends)
+    )
@@
-        writer_start = arm.get("writer_start_ns")
-        writer_end = arm.get("writer_end_ns")
-        writer_valid = (type(writer_start) is int and type(writer_end) is int
-                        and 0 < writer_start < writer_end)
+        writer_start = arm.get("writer_start_ns")
+        writer_end = arm.get("writer_end_ns")
+        writer_valid = (type(writer_start) is int and type(writer_end) is int
+                        and 0 < writer_start < writer_end)
         if arm.get("writer_error") is not None or not writer_valid:
             errors.append(name + "_writer_receipt")
-        if writer_valid and valid_events and any(
-                event["start_ns"] < writer_start or event["end_ns"] > writer_end
-                for event in pubs):
+        if valid_events and not validate_writer_envelope(writer_start, writer_end, pubs):
             errors.append(name + "_publication_outside_writer_envelope")
@@
-                last_read_end = max(
-                    (row.get("read_end_ns") for row in read_rows
-                     if isinstance(row, dict) and type(row.get("read_end_ns")) is int),
-                    default=None,
-                )
-                if (not exit_rows or type(exit_rows[0].get("exit_ns")) is not int or
-                        exit_rows[0].get("exit_ns", 0) <= 0 or
-                        last_read_end is None or exit_rows[0]["exit_ns"] < last_read_end):
+                if (not exit_rows or
+                        not validate_reader_exit(exit_rows[0].get("exit_ns"), read_rows)):
                     errors.append(name + "_reader_exit_timestamp")
