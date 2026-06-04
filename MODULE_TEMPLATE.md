# Module Spec Template

Use this template before adding a new functional module such as calcium score
or cardiac function.

## Module Identity

- `module_id`:
- `display_name`:
- `clinical_scope`:
- `out_of_scope`:

## Trigger

- Manual hotkey:
- Auto-detect keywords:
- Negative markers:
- Queue item:

## Inputs

- Screen/ROI:
- OCR:
- User override:
- Runtime assets:

## Processing

- Parser or inference:
- Clinical rules:
- Formatting rules:
- Reference lookup:

## Outputs

- Report template:
- Metadata:
- Requested shell actions:

## Required Config

```json
{
  "modules": {
    "module_id": {
      "enabled": true,
      "monitor_idx": 1,
      "roi": {}
    }
  }
}
```

## Tests

- Detector:
- Parser/inference:
- Report formatting:
- Negative trigger/safety:
- Integration smoke:

## Open Questions

- List missing clinical or workflow requirements here.

