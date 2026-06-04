# Release Manifest

## Unreleased

Platform:

- `radiology_auto_reporter`: Unreleased working tree
- Module contract: `v1`
- Supported OS target: Windows 10/11 only
- Packaging spec: `Radiology_Auto_Reporter.spec` onedir build

Included modules:

- DEXA Whole Body: source-workspace parser/capture/output/routing synced
- DEXA BMD: source-workspace parser/capture/output/routing synced
- Calcium Score: source-workspace parser/capture/output/routing synced
- Bone Age: manual-gender module handler synced, workstation verification pending

Runtime assets:

- `ref_img.png`
- `bookmark_map.json`
- external `config.json`
- external Bone Age atlas PDF configured by `bone_age_atlas_path`
- external PDF-XChange Viewer path configured by `bone_age_viewer_path`
- local HuggingFace model cache for BoneAgeAIEngine; model loading is
  `local_files_only`

Build command:

```powershell
Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
& "C:\Users\xray\AppData\Local\Python\bin\python.exe" -m PyInstaller ".\Radiology_Auto_Reporter.spec"
```

Verification:

- Unified local verification gate: `python verify_unified.py`
- Verification gate avoids heavyweight runtime imports until app execution
- Deployment preflight: `python preflight_check.py --strict-external`
- Requirement/evidence matrix: `VERIFICATION_MATRIX.md`
- Single-instance duplicate tray guard unit test: pass
- Entrypoint releases single-instance mutex on normal app exit: pass
- Workstation session log checker: `python workstation_log_check.py <log_file>`
- Hotkey string parsing for `Alt+O`, `Shift+2`, `Shift+B`, `Shift+G`,
  `Scroll Lock`: pass
- Manual-trigger workflow default: background polling disabled by default and
  migration.
- DEXA BMD parser regression for PR/AM percent columns and stray graph `7.0`:
  pass
- DEXA parser, platform routing, and module injection unit tests: pass
- Same-session DEXA/Bone Age/DEXA sequence regression test: pass
- Settings save/config propagation unit test: pass
- Packaging asset/config validator unit test: pass
- Unified PyInstaller spec asset coverage test: pass
- Bone Age age-formatting and config unit tests: pass
- Workstation same-session checklist: `WORKSTATION_VERIFY.md`
- Full workstation workflow: pending
- Packaging: not finalized

Known risks:

- Clinical workstation behavior must be verified because PDF/RIS actions use
  Win32 focus, clipboard, and external PDF-XChange Viewer.
- Session log is a unified evidence aid, not a replacement for RIS/PACS/PDF
  workstation verification.
- Auto-detect remains optional in `main.py`, but is disabled by default for the
  current manual-trigger clinical workflow.
