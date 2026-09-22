# Review image qualification — retained experiment

Retrospective evidence delivery for Issue #4080. This is not a new formal run or public preregistration.

Start with `RESULT.md` and `PUBLICATION_NOTE.md`. The complete original 556-file source/raw/construction/audit tree is losslessly reconstructed from the 12 Base64 parts declared in `PACK.json`:

```sh
python -B unpack.py /tmp/review-image-contract-4080
```

The unpacker restores data only. Do **not** rerun the consumed `formal-01` experiment. The original action/result records remain authoritative; image qualification is a separate read-only presentation property and grants no input/replay authority.
