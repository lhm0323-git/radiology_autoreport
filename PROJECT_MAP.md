# Project Map: Radiology Auto Reporter

This folder is the unified target for multiple radiology auto-reporting
modules.

## Runtime Target

- Windows 10/11 clinical workstation.
- Windows 7 compatibility files and virtual environments are no longer part
  of the active project.

## Shared Shell

- `main.py`
  - Qt tray app, hotkeys, worker queue, RIS scan dispatch, module routing,
    optional auto-detect polling, `Scroll Lock` suspend/resume, and shared
    session log window.
  - Owns one unified tray/session for DEXA, Calcium Score, and Bone Age.

- `config_manager.py`
  - Unified config defaults and migration.
  - Owns shared and module-specific config keys.

- `settings_ui.py`
  - Unified settings UI with General, DEXA, and Bone Age sections/tabs.

- `setup_wizard.py`
  - Interactive ROI calibration overlays for RIS OCR, BMD, Whole Body, Calcium,
    and RIS paste focus on new workstation deployments.

- `capture.py`
  - Shared screen capture helpers.
  - Includes DEXA ROI capture and Bone Age ROI capture.

- `ocr_engine.py`
  - Lazy RapidOCR wrapper with configurable thread count and warm-up.

- `output.py`
  - Clipboard/RIS paste behavior.

## Modules

### DEXA

- `parser.py`
  - DEXA Whole Body, BMD, and Calcium Score OCR parsing/report logic.

- `platform_routing.py`
  - Pure hotkey parsing and RIS-text routing helpers for unified queue
    dispatch.

- `packaging_assets.py`
  - Runtime file/config manifest validator for unified packaging checks.

- `Radiology_Auto_Reporter.spec`
  - Unified PyInstaller onedir packaging spec.

- `verify_unified.py`
  - Local verification gate for syntax, unit tests, packaging assets, and
    stale hotkey checks.

- `single_instance.py`
  - Windows mutex guard preventing duplicate unified tray instances.

- `workstation_log_check.py`
  - Post-run checker for copied clinical workstation session logs.

- `preflight_check.py`
  - Deployment/offline readiness checker for package assets, external paths,
    and local HuggingFace cache.

### Bone Age

- `ai_engine.py`
  - Bone Age AI pipeline.

- `bookmark_map.json`
  - Intended atlas page mapping source.

- `ref_img.png`
  - Required histogram matching reference.

## Documentation

- `AGENTS.md`: mandatory rules.
- `ADLC.md`: lifecycle for module evolution and platform integration.
- `ADLC_SUMMARY.md`: compact review guide for the full ADLC workflow.
- `INTEGRATION_CONTRACT.md`: module boundary contract.
- `MODULE_TEMPLATE.md`: template for future modules.
- `MODULE_REGISTRY.md`: module status table.
- `COMPATIBILITY_MATRIX.md`: platform/module compatibility.
- `RELEASE_MANIFEST.md`: current release/module manifest.
- `CHANGELOG.md`: notable changes.
- `PROJECT_MAP.md`: this file.
- `TASKS.md`: multi-agent task list and prompts.

## Module Boundary

- `modules/base.py`
  - Shared `ModuleContext` and `ModuleResult` dataclasses.

- `modules/dexa.py`
  - DEXA Whole Body/BMD/Calcium handler and BMD T/Z toggle cache.

- `modules/bone_age.py`
  - Bone Age handler and age-formatting logic.

- `tests/test_bone_age_module.py`
  - Deterministic tests for Bone Age age range/bookmark formatting.

- `tests/test_dexa_parser.py`
  - Synced DEXA parser tests from the standalone source workspace.

- `tests/test_dexa_platform_integration.py`
  - DEXA module contract test for shared capture/OCR/paste injection.

- `tests/test_platform_routing.py`
  - Unified hotkey queue and RIS-mode routing tests.

- `tests/test_settings_ui_config.py`
  - Settings save/config propagation test for unified hotkeys and monitors.

- `tests/test_packaging_assets.py`
  - Runtime asset/config completeness test for packaging.

- `tests/test_same_session_queue.py`
  - Same-session DEXA/Bone Age/DEXA regression test using shared
    capture/OCR/paste injection.

- `tests/test_workstation_log_check.py`
  - Unit tests for workstation session log evidence parsing.

- `WORKSTATION_VERIFY.md`
  - Manual clinical workstation same-session verification checklist.

- `VERIFICATION_MATRIX.md`
  - Requirement-to-evidence matrix for completion audit.

## Generated or Rebuildable

- `venv/`
- `build/`
- `dist/`
- `__pycache__/`
- local screenshots such as `test_hand.png`, `test_f.png` unless used as
  explicit fixtures.

## Source Workspace References

- `../dexa_reporter`: DEXA source history and ADK files.
- `../bone_age_reporter`: Bone Age source history and ADK files.
