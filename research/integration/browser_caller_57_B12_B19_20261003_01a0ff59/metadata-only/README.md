# Browser caller B12–B19: metadata only

The five original metadata blobs are unchanged from PR #7191 head 39f60fd209bda493a78752766256c81497101efd. Their original README and checksum file describe the full package; SAVED_UNITS.json is intentionally absent from main. The six original files are retained locally on the workstation, and remain in the already-public source PR history; this copy does not remove that publication.

Six ZIP CRC/archive hashes, all 841 member sizes and SHA-256 values, and nine audit-source sizes/SHA-256 values were checked. A decoded scan found user-profile paths in 29 members or audit sources. No actor or original auditor was rerun.

B12 records changed meaning under the same DOM ID; B17 rejects synthetic activation for a trusted-input application. B18/B19 use an application-owned guard with native input, not a generic atomic input primitive. The first B16 setup defect remains distinct. No broad safety, task efficacy, or resource-economics claim follows.
