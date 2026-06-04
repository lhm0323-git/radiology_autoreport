# Module Integration Contract

Every functional module must integrate through this contract. Independent
module development is encouraged, but unified integration must use the shared
shell boundaries.

## Module Identity

Each module must define:

- `module_id`: stable snake_case id, such as `dexa_bmd` or `bone_age`.
- `display_name`: UI label.
- `clinical_scope`: what report draft the module produces.
- `out_of_scope`: what it must not decide or modify.

## Trigger Contract

Each module must declare:

- manual hotkey task type
- auto-detect keywords or detector function
- negative markers to prevent self-triggering
- target monitor and ROI config keys
- expected task queue tuple

Current queue format:

```text
(task_type: str, param: any)
```

Known task types:

- `dexa_wb`
- `dexa_bmd`
- `bone_age`

## Input Contract

Allowed inputs:

- configured screen ROI capture
- OCR text from configured ROI
- local runtime assets
- explicit user hotkey override

Forbidden unless explicitly approved:

- direct PACS/DICOM network query
- hospital DB writes
- external cloud APIs
- persistent identifiable patient screenshots or OCR text

## Processing Contract

A module may implement:

- deterministic parsing
- local AI inference
- report formatting
- local reference lookup such as PDF page selection

Shared shell should own:

- final paste behavior
- global hotkey registration
- shared config persistence
- shared worker queue

## Output Contract

Modules should produce report text and metadata. Legacy code may still perform
side effects inline, but migration should move toward explicit actions.

Recommended future result shape:

```python
{
    "module_id": "bone_age",
    "report_text": "...",
    "metadata": {},
    "actions": [
        {"type": "open_reference_pdf", "page": 90},
        {"type": "paste_report"}
    ]
}
```

## Test Contract

Each module should include:

- detector tests
- parser/inference boundary tests
- report formatting tests
- safety/negative-trigger tests
- representative golden fixtures where feasible

Clinical changes require test updates.

