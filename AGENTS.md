# Radiology Auto Reporter Agent Rules

This project is the unified Windows desktop shell for multiple radiology
auto-reporting modules.

## Architecture

The shell owns:

- app lifecycle and tray icon
- hotkey registration
- worker queue and task routing
- shared config load/migration
- shared OCR and screen capture wrappers
- shared clipboard/RIS paste
- settings UI shell
- packaging/deployment conventions

Functional modules own:

- modality-specific trigger logic
- modality-specific parser or AI inference
- report template and formatting rules
- module-specific runtime assets
- module-specific tests and fixtures

Do not add new modality logic directly into shared shell code without defining
or updating the module contract first.

## Existing Modules

- DEXA Whole Body
- DEXA BMD
- Bone Age

Planned examples:

- Calcium score
- Cardiac function

## Hard Rules

- Never write directly to hospital databases.
- Never query PACS/DICOM networks unless explicitly approved.
- Never store identifiable screenshots or OCR text unless explicitly approved.
- Never add diagnosis/treatment recommendations outside approved templates.
- Any clinical logic change requires tests or golden fixtures.
- Supported workstation target is Windows 10/11 only. Do not add Windows 7
  compatibility work unless the project is explicitly re-scoped.
- Do not treat source workspaces (`../dexa_reporter`, `../bone_age_reporter`)
  as the unified runtime without checking this folder.

## Context Loading

For any task, read:

1. `AGENTS.md`
2. `INTEGRATION_CONTRACT.md`
3. `MODULE_REGISTRY.md`
4. `PROJECT_MAP.md`
5. The relevant module handoff/spec
6. Only task-relevant source files

Generated artifacts such as `venv/`, `build/`, `dist/`, and `__pycache__/`
are not active project structure.
