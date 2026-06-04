# Agentic Development Lifecycle

This lifecycle keeps the platform stable while functional modules evolve.

## Principle

Functional modules may be developed independently, but integration into
`radiology_auto_reporter` must happen through the shared module contract, not
by copying whole applications into `main.py`.

## Phase 1: Module Development

Module agents may iterate inside source workspaces such as:

- `../dexa_reporter`
- `../bone_age_reporter`
- future module folders

Each module workspace should maintain:

- `AGENTS.md`
- `AGENT_HANDOFF.md`
- `PROJECT_MAP.md`
- `TASKS.md`
- module-specific specs/tests

## Phase 2: Contract Check

Before integration, a module must declare:

- `module_id`
- module version
- contract version
- config schema changes
- runtime assets
- dependencies
- side effects
- tests or manual verification performed

## Phase 3: Platform Integration

Platform agents update:

- `MODULE_REGISTRY.md`
- `COMPATIBILITY_MATRIX.md`
- config migration if needed
- settings UI if needed
- task routing/module registry if needed
- integration tests or smoke checks

## Phase 4: Release

Release notes must list:

- platform version
- supported OS target
- module versions
- contract version
- runtime assets
- migration notes
- known risks
- verification status

## Gates

A module can enter the platform only when:

- it matches `INTEGRATION_CONTRACT.md`
- its config changes are backward-compatible or migrated
- clinical/report logic changes have tests or explicit manual verification
- generated artifacts are excluded from active structure
- source workspace differences are documented
