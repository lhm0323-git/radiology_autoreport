# Module Registry

This registry tells agents which modules exist, where their source history
lives, and what is verified.

| Module | Status | Source Workspace | Unified Status | Key Files | Test Status |
|---|---|---|---|---|---|
| DEXA Whole Body | newer source workspace | `../dexa_reporter` | parser/capture/output/routing synced | `modules/dexa.py`, `parser.py`, `capture.py`, `output.py`, `platform_routing.py` | unified parser/routing/module tests pass; workstation end-to-end pending |
| DEXA BMD | newer source workspace | `../dexa_reporter` | parser/capture/output/routing synced | `modules/dexa.py`, `parser.py`, `capture.py`, `output.py`, `platform_routing.py` | unified parser/routing/module tests pass; workstation end-to-end pending |
| Bone Age | clinical trial | `../bone_age_reporter` | manual-gender behavior synced | `modules/bone_age.py`, `ai_engine.py`, `capture.py`, `bookmark_map.json`, `ref_img.png` | age-format/config tests pass; workstation end-to-end needs verification |
| Calcium Score | verified source workspace | `../dexa_reporter` | DEXA mode synced | `modules/dexa.py`, `parser.py`, `capture.py`, `output.py`, `platform_routing.py` | unified parser/routing/module tests pass; workstation end-to-end pending |
| Cardiac Function | planned | TBD | not started | TBD | none |

## Source Workspace Docs

- DEXA: `../dexa_reporter/AGENTS.md`, `../dexa_reporter/AGENT_HANDOFF.md`.
- Bone Age: `../bone_age_reporter/AGENTS.md`,
  `../bone_age_reporter/AGENT_HANDOFF.md`,
  `../bone_age_reporter/MERGE_NOTES.md`.

## Needs Verification

- Bone Age requires explicit `shift+b` male or `shift+g` female routing; no
  automatic gender inference is used for clinical execution.
- Bone Age uses a default calibration offset of `-5.0` months and local-only
  HuggingFace model loading. Deployment machines need the model cache bundled
  or preloaded.
- Unified DEXA uses `Alt+O` RIS scan routing, `shift+2` BMD T/Z toggle, and
  shared capture/OCR/paste services. Workstation same-session validation is
  still required.
- Unified DEXA + Bone Age sequential clinical run is not documented as complete.
- Packaging strategy for the unified app is not finalized.
