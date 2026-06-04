# Compatibility Matrix

| Platform | Contract | DEXA Whole Body | DEXA BMD | Bone Age | Notes |
|---|---|---|---|---|---|
| Unreleased, Windows 10/11 | v1 | source workspace stable-ish | source workspace stable-ish | clinical trial | First module boundary added; full workstation verification pending; Windows 7 unsupported |

## Contract Versions

- `v1`: task queue uses `(task_type: str, param: any)` and module handlers
  return `ModuleResult` with report text, metadata, and action requests.

## Needs Verification

- Unified app end-to-end run on the clinical workstation.
- Bone Age PDF atlas page jump after module extraction.
- DEXA Whole Body and BMD paste behavior after module extraction.
