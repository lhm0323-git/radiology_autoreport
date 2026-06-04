# Radiology Auto Reporter Tasks and Multi-Agent Prompts

## Priority Tasks

### Task 1: Baseline Module Inventory

Acceptance:

- Confirm current unified files and source workspace files.
- Mark DEXA/Bone Age features as implemented, partial, or Needs verification.
- Do not modify code.

### Task 2: Bone Age Bookmark Map Wiring Plan

Acceptance:

- Determine whether `bookmark_map.json` is currently wired.
- Propose a small migration from hardcoded mapping to JSON.
- Preserve all existing page numbers.

### Task 3: Module Boundary Refactor Plan

Acceptance:

- Keep moving module-specific logic out of `main.py` after the initial handler extraction.
- Move auto-detect logic into module-specific detector functions.
- Keep DEXA and Bone Age behavior verifiable after each step.

### Task 4: New Module Spec

Acceptance:

- Use `MODULE_TEMPLATE.md`.
- Define trigger, input, processing, output, config, tests, and open questions.
- Do not code until clinical rules are clear.

## Prompt Bank

### Coordinator Agent Prompt

```text
你是 radiology_auto_reporter 的 coordinator agent。

請閱讀：
- AGENTS.md
- INTEGRATION_CONTRACT.md
- MODULE_REGISTRY.md
- PROJECT_MAP.md
- ../dexa_reporter/AGENT_HANDOFF.md
- ../bone_age_reporter/AGENT_HANDOFF.md
- ../bone_age_reporter/MERGE_NOTES.md

不要改 code。請輸出：
- shared shell 應負責什麼
- DEXA 與 Bone Age 各自負責什麼
- 哪些功能已合併
- 哪些是 Needs verification
- 下一步最小可驗證任務
```

### New Module Designer Prompt

```text
你是 radiology_auto_reporter 的 new module designer。

任務：為 [calcium_score / cardiac_function] 建立 module spec。

請閱讀：
- AGENTS.md
- INTEGRATION_CONTRACT.md
- MODULE_TEMPLATE.md
- MODULE_REGISTRY.md

請先只寫 spec，不寫 code。
Spec 必須包含 clinical scope、out of scope、trigger、inputs、processing、
outputs、required config、tests、open questions。

如果需求不足，請列 Open Questions，不要自行假設臨床規則。
```

### Module Migration Worker Prompt

```text
你是 radiology_auto_reporter 的 module migration worker。

任務：把 [dexa / bone_age] 從 source workspace 整理成 unified module。

請閱讀：
- AGENTS.md
- INTEGRATION_CONTRACT.md
- MODULE_REGISTRY.md
- 該 module 的 AGENT_HANDOFF.md / MERGE_NOTES.md
- main.py
- config_manager.py
- settings_ui.py

請先輸出 migration plan：
- 哪些功能已在 unified 存在
- 哪些尚未合併
- 哪些檔案是 source of truth
- 哪些檔案可 archive
- 最小可驗證整合步驟

不要先改 code。
```

### Reviewer Prompt

```text
你是 radiology_auto_reporter 的 code reviewer。

請 review 最近變更，優先找：
- module boundary 是否被破壞
- clinical/report formatting logic 是否無測試被改動
- 是否把 source workspace 舊行為誤當 unified 現況
- 是否新增未授權 PACS/DICOM network 或 DB write
- 是否把 venv/build/dist/__pycache__ 當 active structure

請先列 findings，依嚴重度排序。
```
