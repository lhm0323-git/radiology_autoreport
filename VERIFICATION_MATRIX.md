# Verification Matrix

This matrix maps the current integration goal to concrete evidence. It is
intended for completion audit before marking the unified DEXA + Bone Age
workflow complete.

| Requirement | Current Evidence | Status |
|---|---|---|
| One unified tray app, not two module apps | `main.py` owns one tray icon; `single_instance.py` blocks duplicate launches; `tests/test_single_instance.py` and `tests/test_main_entrypoint.py` pass | Automated pass; workstation visual confirmation pending |
| DEXA + Bone Age run in one app session | `tests/test_same_session_queue.py` runs DEXA BMD -> Bone Age -> DEXA toggle -> DEXA Calcium with shared context | Automated pass; workstation same-session log pending |
| Hotkey queue routing | `platform_routing.py`; `tests/test_platform_routing.py`; stale hotkey scan in `verify_unified.py` | Automated pass |
| Hotkey string parsing | `parse_hotkey()` tests cover `Alt+O`, `Shift+2`, `Shift+B`, `Shift+G`, `Scroll Lock` | Automated pass |
| Module contract | `modules/base.py`; `DexaModule.run()` and `BoneAgeModule.run()` return `ModuleResult`; module integration tests pass | Automated pass |
| Settings tabs pass config correctly | `tests/test_settings_ui_config.py` verifies DEXA/Bone Age hotkeys, monitors, and Bone Age offset save behavior | Automated pass |
| Shared capture/OCR/paste injection | `tests/test_dexa_platform_integration.py` and `tests/test_same_session_queue.py` use shared `ModuleContext` fakes | Automated pass |
| Bone Age manual gender only | `modules/bone_age.py`; `tests/test_bone_age_module.py`; stale auto trigger scan | Automated pass |
| Bone Age atlas assets | `bookmark_map.json`, `ref_img.png`, `packaging_assets.py`, `tests/test_packaging_assets.py` | Automated pass |
| Local-only Bone Age model loading | `ai_engine.py` uses `local_files_only=True`; `preflight_check.py --strict-external` checks local HF cache | Code evidence pass; deployment cache smoke pending |
| DEXA RIS scan and BMD toggle | `platform_routing.py`, `modules/dexa.py`, parser tests, same-session test | Automated pass; workstation RIS OCR/paste pending |
| DEXA BMD score extraction avoids PR/AM percent columns | `parse_bmd_v2()` only treats actual T-score/Z-score headers as score columns; regression tests cover PR/Peak Reference, AM/Age Matched, and stray `7.0` graph noise | Automated pass; workstation spot check pending |
| Manual-trigger workflow, no background polling | `default_config()` and config migration set `auto_detect.enabled = False`; settings UI defaults unchecked | Automated pass; workstation settings confirmation pending |
| Suspend/resume hotkey | `scroll_lock` is default platform suspend hotkey and remains registered while clinical hotkeys are paused | Automated pass; workstation hotkey confirmation pending |
| Calcium Score DEXA mode | `tests/test_dexa_parser.py`, `tests/test_dexa_platform_integration.py`, same-session test | Automated pass; workstation RIS OCR/paste pending |
| Shared session log | `main.py` tray action `Show Session Log`; RIS scan/PDF navigation/Done events use `log_event`; `WORKSTATION_VERIFY.md`; `workstation_log_check.py` | Code evidence pass; copied workstation log pending |
| Packaging assets complete | `Radiology_Auto_Reporter.spec`; `packaging_assets.py`; `tests/test_packaging_assets.py` | Automated pass; PyInstaller build smoke pending |
| No RIS/PACS/PDF focus interference | Requires clinical workstation sequence in `WORKSTATION_VERIFY.md` and `workstation_log_check.py` PASS | Pending external evidence |

## Completion Rule

The goal is not complete until the pending workstation evidence is collected:

- `verify_unified.py` ends with `unified platform checks: PASS`.
- The app starts with one tray icon.
- `Show Session Log` records DEXA -> Bone Age -> DEXA in the same process.
- `workstation_log_check.py <copied_log>` returns `PASS`.
- The copied log includes DEXA Done, Bone Age Done, and Bone Age PDF navigation
  evidence.
- RIS paste succeeds after each DEXA/Bone Age task.
- Bone Age PDF-XChange page navigation succeeds.
- Packaging smoke build is run if deployment readiness is being claimed.
