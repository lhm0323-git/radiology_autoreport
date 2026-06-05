# Agent Handoff: Radiology Auto Reporter

Updated: 2026-06-05

This is the active unified clinical runtime for radiology auto-reporting. It
integrates DEXA Whole Body, BMD, Calcium Score, and Bone Age into one Windows
tray app.

## Current Role

- This folder is the deployment source of truth.
- `../dexa_reporter` and `../bone_age_reporter` are source-history/module-lab
  workspaces.
- Future module upgrades can be developed independently, but deployment changes
  should land here and pass the unified tests.

## Current Stable Workflow

Hotkeys:

- `Alt+O`: scan RIS title ROI and route DEXA/Calcium mode.
- `Shift+2`: toggle previous BMD report T/Z mode without rerunning OCR.
- `Shift+B`: Bone Age with male gender.
- `Shift+G`: Bone Age with female gender.
- `Scroll Lock`: suspend/resume app hotkeys. On suspend, Bone Age AI model is
  unloaded to reduce memory after Bone Age use.

Clinical mode:

- Background polling is disabled by default.
- Operator prepares RIS/PACS, then triggers manually.
- All OCR and AI inference are local. No PACS/DICOM network calls are used.
- Report paste uses clipboard and optional RIS focus click.

## Included Modules

### DEXA BMD

- Triggered by RIS title routing through `Alt+O`.
- Parser handles T-score/Z-score columns and avoids PR/AM percent columns.
- Ignores graph/QC numeric artifacts such as stray `7.0`.
- Uses lowest valid diagnostic site.
- `Shift+2` toggles last BMD report between T and Z mode from cache.

### DEXA Whole Body / Body Composition

- Triggered by RIS title routing through `Alt+O`.
- Extracts fat percent, VAT area, appendicular lean/height2, and A/G ratio.
- Report template is editable.
- Current default template has blank lines between sections 1-4.

### Calcium Score

- Triggered by RIS title routing through `Alt+O`.
- Extracts LM, LAD, CX/LCX, RCA, and Total from score table.
- Skips patient-info OCR to improve speed.
- Report is Agatston score formatting only; no risk category or treatment
  recommendation is added.

### Bone Age

- Triggered only by explicit gender hotkeys `Shift+B` / `Shift+G`.
- Gender OCR is not used clinically.
- Captures calibrated `roi_bone_age`.
- Uses local-only HuggingFace models:
  - `ianpan/bone-age-crop`;
  - `ianpan/bone-age`.
- Current calibration offset: `-5.0` months.
- Uses `bookmark_map.json` for atlas page mapping.
- Opens/jumps PDF-XChange Viewer to atlas page.
- `Scroll Lock` unloads model after use; next Bone Age run lazy-loads again.

## Architecture

Shared shell:

- `main.py`: tray app, hotkeys, worker queue, RIS scan dispatch, PDF navigation,
  session log, suspend/resume, Bone Age model unload.
- `config_manager.py`: default config and migration.
- `settings_ui.py`: settings tabs and report template editors.
- `setup_wizard.py`: ROI calibration overlays.
- `capture.py`: DEXA and Bone Age screen capture.
- `ocr_engine.py`: lazy RapidOCR wrapper with startup warm-up.
- `output.py`: clipboard/RIS paste.

Module boundary:

- `modules/base.py`: `ModuleContext`, `ModuleResult`.
- `modules/dexa.py`: DEXA/Calcium module and BMD toggle cache.
- `modules/bone_age.py`: Bone Age module and age formatting.
- `parser.py`: DEXA/Calcium parsing, clinical logic, and RIS title routing.
- `platform_routing.py`: hotkey and task routing helpers.

## Configuration

Important config keys:

- `hotkeys.start_scan`: default `alt+o`.
- `hotkeys.toggle_bmd`: default `shift+2`.
- `hotkeys.force_male`: default `shift+b`.
- `hotkeys.force_female`: default `shift+g`.
- `hotkeys.suspend`: default `scroll_lock`.
- `monitors.dexa_wb`, `dexa_bmd`, `dexa_calcium`, `bone_age`.
- `auto_detect.enabled`: default `false`.
- `auto_detect.roi`: precise RIS title/report ROI.
- `click_before_paste`: RIS report field focus point.
- `roi_bmd`, `roi_wb`, `roi_calcium`, `roi_bone_age`.
- `whole_body_template`, `bmd_template`, `calcium_template`,
  `bone_age_template`.
- `bone_age_bias_offset_months`: current default `-5.0`.
- `bone_age_atlas_path`, `bone_age_viewer_path`: absolute or portable relative
  paths.

## ROI Calibration

On every new workstation, use tray menu `ROI Calibration`:

- RIS OCR ROI: active report title line only; avoid old exam history.
- RIS Paste Focus: click inside RIS report edit field.
- BMD ROI: patient info and results table.
- Whole Body ROI: patient info and results area.
- Calcium ROI: table area.
- Bone Age Hand ROI: full hand/wrist/distal radius-ulna with small margin.

Use `Reload Config` or restart after calibration.

## Portable Deployment

Portable package output:

```text
dist\Radiology_Auto_Reporter
```

Build command:

```powershell
Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
& "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\package_portable.py" `
  --atlas "D:\download\Atlas_of_Hand_Bone_Age.pdf" `
  --viewer-dir "D:\programs\PDF-XChange Viewer_2.5.311"
```

Portable folder includes:

- `Radiology_Auto_Reporter.exe`
- `_internal\`
- `config.json`
- `bookmark_map.json`
- `ref_img.png`
- `hf_cache\hub\models--ianpan--bone-age-crop`
- `hf_cache\hub\models--ianpan--bone-age`
- `assets\Atlas_of_Hand_Bone_Age.pdf`
- `tools\PDF-XChange Viewer_2.5.311\PDFXCview.exe`
- `README_DEPLOY.txt`

The package is large, about 1.48 GB, because it bundles Python/PyInstaller
runtime, PyQt6, RapidOCR/onnxruntime, OpenCV/numpy/scipy/pandas, Torch,
transformers/timm, Bone Age model cache, atlas PDF, and PDF-XChange Viewer.

## Performance Notes

- DEXA/Calcium normally complete in a few seconds after OCR warm-up.
- Bone Age first use after startup/model unload takes about 10-15 seconds.
- Subsequent Bone Age runs are usually about 1-2 seconds.
- Idle CPU should be near zero.
- High idle memory after Bone Age is expected until `Scroll Lock` unloads the
  model.
- OCR warm-up on startup is intentionally kept to make first DEXA/Calcium run
  fast.

## Verification

Current automated gate:

```powershell
python .\verify_unified.py
python -m unittest discover -s tests
```

Current known status:

- `verify_unified.py`: pass.
- Unit tests: 44 tests pass.
- Clinical workstation workflow has been manually tested for DEXA, Calcium, and
  Bone Age in the unified app.
- PDF jump and RIS paste were tested in the clinical workstation flow.

## Important Debug Lessons

- RIS routing should use active report title line, not broad historical lists.
- OCR title matching must tolerate lost characters such as `文字告`.
- Do not trust patient history text for mode routing.
- Do not kill/reopen PDF-XChange Viewer; reuse existing window to avoid flicker.
- Use clipboard paste for page numbers and RIS reports; IME can intercept typed
  digits.
- Keep `click_before_paste` for same-session focus recovery.
- Do not restore gender OCR for Bone Age clinical execution unless explicitly
  revalidated.
- Do not broaden ROIs for speed without checking OCR misrouting risk.
- Build/dist are generated artifacts and should stay out of git.

## Source Workspace Sync

If upgrading a module:

- DEXA/Calcium source history: `../dexa_reporter/AGENT_HANDOFF.md`.
- Bone Age source history: `../bone_age_reporter/AGENT_HANDOFF.md`.
- Sync into unified files deliberately:
  - `modules/dexa.py`
  - `modules/bone_age.py`
  - `parser.py`
  - `capture.py`
  - `setup_wizard.py`
  - `config_manager.py`
  - tests

## Future Development

Recommended:

- Add more real OCR fixtures for BMD, Whole Body, and Calcium Score.
- Add workstation log export/import convenience around `workstation_log_check.py`.
- Improve package size only after proving no runtime dependency breaks.
- Add Bone Age calibration reporting by age/sex bins if enough corrected labels
  are collected.
- Consider optional manual tray action `Unload Bone Age AI` if `Scroll Lock`
  unload is not explicit enough for users.
- Keep module additions behind the `ModuleContext` / `ModuleResult` contract.

Not currently planned:

- Background polling as default clinical path.
- PACS/DICOM network access.
- LLM-based report generation.
- Treatment or risk recommendations outside approved templates.
