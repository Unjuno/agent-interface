FROM issue-3676-audit-hardening:formal@sha256:b138c00ce990cf972f8be1ae4b3f7a11a198ad46e8804b41dabd979052aad8e8
WORKDIR /work
COPY research/audits/issue_3688_raw_byte_binding_v1/raw_byte_audit.py research/audits/issue_3688_raw_byte_binding_v1/test_raw_byte_binding.py research/audits/issue_3688_raw_byte_binding_v1/independent_audit.py /work/
RUN chmod 0555 /work/raw_byte_audit.py /work/test_raw_byte_binding.py /work/independent_audit.py
