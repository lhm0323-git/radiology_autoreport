# ADLC Summary: Platform + Modules + Integration Contract

This project uses an Agentic Development Lifecycle (ADLC) where each radiology
workflow can mature independently before entering the unified platform.

## Mental Model

```text
functional module workspace
  dexa_reporter/
  bone_age_reporter/
  calcium_score_reporter/
  cardiac_function_reporter/
        |
        v
module spec + handoff + tests + version notes
        |
        v
integration contract gate
        |
        v
radiology_auto_reporter/
  stable shared shell
  modules/
  module registry
  release manifest
```

Functional modules may evolve quickly. The platform should remain stable and
only accept module versions that satisfy the integration contract.

## Folder Roles

### Module Workspaces

Examples:

- `dexa_reporter/`
- `bone_age_reporter/`
- future `calcium_score_reporter/`
- future `cardiac_function_reporter/`

Use module workspaces for:

- rapid prototyping
- clinical rule exploration
- workstation-specific debugging
- OCR/parser/AI experiments
- module-specific fixtures and tests
- handoff/spec documentation

Do not use the unified platform as the daily experiment folder.

### Unified Platform

Folder:

- `radiology_auto_reporter/`

The platform owns:

- app lifecycle
- tray icon
- hotkeys
- Windows 10/11 runtime target
- worker queue
- config load/migration
- settings UI shell
- shared OCR/capture/output wrappers
- module registry
- platform release notes
- integration tests/smoke checks

The platform should not absorb unfinished module experiments.

## Layer Responsibilities

### Platform Layer

Owns shared runtime behavior:

- `main.py`
- shared queue and task routing
- shared settings UI
- shared config manager
- shared paste/output side effects
- packaging/release manifest

### Functional Module Layer

Owns modality-specific behavior:

- detector logic
- parser or AI inference
- report template
- clinical formatting rules
- module-specific runtime assets
- module-specific fixtures/tests

Examples:

- DEXA BMD / Whole Body
- Bone Age
- Calcium Score
- Cardiac Function

### Integration Contract Layer

Defines how a module enters the platform:

- `module_id`
- trigger/hotkey
- detector/negative markers
- input contract
- output contract
- config schema
- runtime assets
- allowed side effects
- required tests

See:

- `INTEGRATION_CONTRACT.md`
- `MODULE_TEMPLATE.md`
- `MODULE_REGISTRY.md`

## Module Maturity Stages

```text
Stage 0: idea
Only clinical need and open questions exist.

Stage 1: prototype
Can run manually in its own workspace. Rough edges are expected.

Stage 2: module-stable
Has MODULE_SPEC, fixtures, basic tests, and clear clinical rules.

Stage 3: integration-ready
Matches INTEGRATION_CONTRACT and can be wrapped as a module handler.

Stage 4: platform-integrated
Lives in radiology_auto_reporter/modules and passes smoke checks.

Stage 5: release-ready
Listed in RELEASE_MANIFEST and verified on the workstation.
```

Current rough status:

- DEXA: around Stage 3, pending stronger fixtures and unified smoke testing.
- Bone Age: around Stage 2.5 to 3, pending workstation end-to-end verification.

## Versioning Model

Use three version axes:

```text
Platform version:
  radiology_auto_reporter vX.Y.Z

Contract version:
  module_contract v1

Module versions:
  dexa_bmd vX.Y.Z
  dexa_whole_body vX.Y.Z
  bone_age vX.Y.Z
```

Track compatibility in:

- `MODULE_REGISTRY.md`
- `COMPATIBILITY_MATRIX.md`
- `RELEASE_MANIFEST.md`
- `CHANGELOG.md`

## When To Update The Platform

Update `radiology_auto_reporter` only when:

- adding a new module
- changing a module trigger/hotkey/detector
- changing config schema
- adding runtime assets
- adding shared dependencies
- changing module output contract
- adding new allowed side effects
- moving a module from workspace prototype to unified runtime

Do not update the platform for every internal module experiment.

## Standard Integration Flow

```text
1. Develop in module workspace
2. Update module AGENTS / HANDOFF / MODULE_SPEC / TEST_PLAN
3. Run module-level tests or manual verification
4. Prepare integration plan
5. Check against INTEGRATION_CONTRACT
6. Update platform registry/config/UI/routing if needed
7. Add or update platform tests
8. Update release docs
9. Run platform smoke checks
```

## New Module Workspace Starter

For a new module such as calcium score:

```text
calcium_score_reporter/
  AGENTS.md
  MODULE_SPEC.md
  AGENT_HANDOFF.md
  PROJECT_MAP.md
  TASKS.md
  TEST_PLAN.md
  CHANGELOG.md
  MERGE_NOTES.md
  fixtures/
  tests/
```

Optional, depending on module type:

```text
  parser.py
  ai_engine.py
  capture.py
  assets/
  config.json
```

## Prompt: Start A New Module

```text
我要建立新的 functional module workspace：[module_name]_reporter。

目標是先獨立開發與測試，不直接改 radiology_auto_reporter。

請建立以下 ADK 文件：
- AGENTS.md
- MODULE_SPEC.md
- AGENT_HANDOFF.md
- PROJECT_MAP.md
- TASKS.md
- TEST_PLAN.md
- CHANGELOG.md
- MERGE_NOTES.md

請依照 ../radiology_auto_reporter/INTEGRATION_CONTRACT.md 和 MODULE_TEMPLATE.md 設計。
目前需求若不足，請列 Open Questions，不要自行假設臨床規則。
不要寫大量程式碼，先建立 workspace skeleton 和 spec。
```

## Prompt: Evaluate Module For Integration

```text
這個 module workspace 已完成一輪 prototype。
請評估是否可整合進 radiology_auto_reporter。

請閱讀：
- radiology_auto_reporter/AGENTS.md
- radiology_auto_reporter/ADLC.md
- radiology_auto_reporter/INTEGRATION_CONTRACT.md
- radiology_auto_reporter/MODULE_REGISTRY.md
- [module]/MODULE_SPEC.md
- [module]/AGENT_HANDOFF.md
- [module]/TEST_PLAN.md
- [module]/CHANGELOG.md

請輸出 integration plan：
- module_id / version / contract version
- 需要的 config keys
- 需要的 runtime assets
- trigger / detector
- input/output contract
- side effects
- 需要改 radiology_auto_reporter 哪些檔案
- 最小可驗證步驟
- 不能整合的 blocker

不要先改 code。
```

## Prompt: Platform Integration Agent

```text
你是 radiology_auto_reporter 的 platform integration agent。

任務：評估 [module_name] 從 version X 升到 version Y 是否可以整合進平台。

請閱讀：
- radiology_auto_reporter/AGENTS.md
- radiology_auto_reporter/ADLC.md
- radiology_auto_reporter/INTEGRATION_CONTRACT.md
- radiology_auto_reporter/MODULE_REGISTRY.md
- radiology_auto_reporter/COMPATIBILITY_MATRIX.md
- [module]/CHANGELOG.md
- [module]/AGENT_HANDOFF.md
- [module]/TEST_PLAN.md

請輸出：
- contract 是否相容
- config schema 是否改變
- runtime assets 是否改變
- shared dependencies 是否改變
- side effects 是否改變
- 需要更新 platform 哪些文件或程式
- 最小整合步驟
- 必須跑哪些測試

不要直接改 code，先提出 integration plan。
```

## Rules Of Thumb

- Prototype in module folders.
- Integrate only through the contract.
- Keep platform stable.
- Keep module experiments out of release candidates.
- Treat clinical logic changes as test-required changes.
- Mark conflicts as `Needs verification`.
- Keep generated artifacts out of active project structure.

## One-Sentence Principle

Fast incubation, strict integration, conservative release.
