# Pinned Unicode data inputs

The two official Unicode 18.0.0 text inputs are not rehosted by this study.
Retrieve these exact files into the study source directory before candidate or
audit execution, then verify SHA-256 before use:

| File | Official URL | SHA-256 |
|---|---|---|
| `confusables.txt` | https://www.unicode.org/Public/security/18.0.0/confusables.txt | `6ED3EE967C9DFDF6677D563C9985182FBC50A2EFB7D6059CD57B2E2CE18F5B92` |
| `DerivedCoreProperties.txt` | https://www.unicode.org/Public/18.0.0/ucd/DerivedCoreProperties.txt | `09C928886A178FCAFD93C29E4BD59073A058E5A100B716D425CB563AB50F68C9` |

The hashes are also enforced independently by `simulate.py` and `audit.py`.
No network retrieval occurs during either run. Unicode data version is 18.0.0;
Python's bundled normalization tables are reported separately because the
selected interpreter ships Unicode Character Database 15.0.0.
