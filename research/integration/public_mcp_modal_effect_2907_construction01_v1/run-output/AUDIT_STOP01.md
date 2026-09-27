# Independent audit container STOP01

The read-only auditor did not reach evidence validation. The Docker bind mount was already present at `/audit`, while auditor v1 creates its second argument with `exist_ok=False`; invoking it with output argument `/audit` therefore exited 1:

```text
FileExistsError: [Errno 17] File exists: '/audit'
```

Evidence was mounted read-only and unchanged. This is an auditor-output mount-path setup STOP, not an audit verdict. A separate read-only auditor container will use an absent child directory under the same dedicated writable audit mount; auditor source bytes remain unchanged.
