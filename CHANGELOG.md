# Changelog

## Unreleased

- Added ADK documents for the unified platform.
- Added module integration contract, registry, and template.
- Added first module boundary implementation:
  - `modules/base.py`
  - `modules/dexa.py`
  - `modules/bone_age.py`
- Moved DEXA and Bone Age task execution out of `main.py` into module handlers.
- Added deterministic Bone Age age-formatting tests.
- Synced verified Bone Age clinical routing into the unified app:
  - manual gender only via `shift+b` male and `shift+g` female
  - removed the generic Bone Age auto trigger
  - default calibration offset set to `-5.0` months
  - model loading constrained to local HuggingFace cache
- Synced DEXA source-workspace behavior into the unified app:
  - `Alt+O` RIS scan routes Whole Body, BMD, and Calcium modes
  - `shift+2` toggles the previous BMD report T/Z mode
  - DEXA parser, capture, OCR, and paste timing behavior match the newer
    standalone workspace
  - DEXA, Bone Age, and Calcium tasks run through one shared queue and tray app
- Removed remaining Windows 7/`venv_win7` documentation references from the
  active platform target.
