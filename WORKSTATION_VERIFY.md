# Workstation Verification: Unified DEXA + Bone Age Session

Use this checklist on the clinical workstation after unit tests pass. The
objective is to prove DEXA and Bone Age run in the same `radiology_auto_reporter`
app session without hotkey, queue, clipboard, OCR, capture, or PDF focus
interference.

See `VERIFICATION_MATRIX.md` for the requirement-to-evidence audit.

## Expected App Shape

- One tray icon: `Radiology Auto-Reporter`.
- One settings dialog with `General`, `DEXA`, and `Bone Age` tabs.
- One shared session log from tray menu `Show Session Log`.
- One worker queue in one Python process.
- Duplicate launches are blocked by a single-instance guard.
- Background polling is disabled by default; DEXA/Bone Age run by physician
  hotkey trigger after PACS/RIS is ready.
- No standalone `dexa_reporter` or `bone_age_reporter` process should be
  running during this verification.

## Hotkeys

- `Alt+O`: scan RIS text and dispatch DEXA Whole Body, BMD, or Calcium.
- `Shift+2`: toggle the previous BMD report between T-score and Z-score.
- `Shift+B`: run Bone Age with male gender.
- `Shift+G`: run Bone Age with female gender.
- `Scroll Lock`: suspend or resume platform hotkeys.

## Sequence

1. Run local platform verification:

   ```powershell
   Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
   & "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\verify_unified.py"
   ```

   Expected final line: `[verify] unified platform checks: PASS`.

   For deployment/offline readiness, also run:

   ```powershell
   & "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\preflight_check.py" --strict-external
   ```

   Expected final line: `PASS`.

2. Start unified app:

   ```powershell
   Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
   & "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\main.py"
   ```

3. Confirm startup:
   - Tray icon appears once.
   - Console prints `Radiology Auto-Reporter running.`
   - Console prints `Engines Initialized.`
   - Tray menu `Show Session Log` shows the same unified session events.

4. Open settings:
   - General tab shows `Enable Background Polling` unchecked.
   - General tab shows `Suspend / Resume = scroll_lock`.
   - DEXA tab shows `RIS Scan Trigger = alt+o`.
   - DEXA tab shows `BMD T/Z Toggle = shift+2`.
   - Bone Age tab shows `Force Male Trigger = shift+b`.
   - Bone Age tab shows `Force Female Trigger = shift+g`.
   - Bone Age calibration offset is `-5.0`.

   For a new workstation or a changed monitor layout, use tray menu
   `ROI Calibration` before clinical testing:
   - `Full DEXA Setup Wizard`: monitor mapping plus RIS, DEXA, and paste ROIs.
   - `RIS OCR ROI`: RIS order text area used by `Alt+O`.
   - `BMD ROI`: BMD patient info and results table.
   - `Whole Body ROI`: Whole Body patient info and results table.
   - `Calcium ROI`: Calcium patient info and score table.
   - `RIS Paste Focus`: report text field click point used before paste.

5. Focus RIS/PACS target window and confirm hotkeys enable:
   - Console prints `RIS Window Detected (...). Hotkeys Enabled.`

6. DEXA BMD:
   - Put a BMD order/report context in the RIS ROI.
   - Press `Alt+O`.
   - Expected log:
     - `[Scan RIS] Mode identified` or `[Scan RIS] Dispatching task`
     - `Processing Task: dexa`
     - `DEXA Done!`
   - RIS report text is pasted correctly.

7. DEXA BMD toggle:
   - Without rerunning capture/OCR, press `Shift+2`.
   - Expected log:
     - `Processing Task: dexa_toggle`
   - RIS report changes between T-score and Z-score wording.

8. Bone Age:
   - Focus Bone Age PACS image.
   - Press `Shift+B` or `Shift+G` based on physician-confirmed gender.
   - Expected log:
     - `Processing Task: bone_age`
     - `Gender forced to: Male/Female`
     - `Predicted Age: raw=..., offset=-5.00 months`
     - `Bone Age Done!`
   - RIS report text is pasted correctly.
   - PDF-XChange Viewer jumps to the expected atlas page.

9. Return to DEXA in the same app session:
   - Focus RIS DEXA case again.
   - Press `Alt+O`.
   - Expected: DEXA still dispatches and pastes normally.

10. Negative checks:
   - Do not expect automatic background polling to trigger DEXA; use `Alt+O`.
   - Press `Scroll Lock`; clinical hotkeys should pause. Press it again to resume.
   - `Shift+2` must not trigger Bone Age.
   - Bone Age must not run without `Shift+B` or `Shift+G`.
   - No second tray icon appears.
   - Starting `main.py` a second time prints duplicate-instance exit text and
     does not create another tray icon.
   - No stale Bone Age PDF focus prevents DEXA RIS paste.
   - No stale DEXA toggle state affects Bone Age.

## Evidence To Record

- Copy the console log covering steps 5-8.
- Copy the shared session log covering steps 5-8.
- Note whether RIS paste succeeded for each module.
- Note whether PDF atlas navigation succeeded for Bone Age.
- Note total runtime if timing logs are present.

After copying the shared session log to a text file, run:

```powershell
Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
& "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\workstation_log_check.py" ".\workstation_session_log.txt"
```

Expected final line: `PASS`.

The checker requires DEXA -> Bone Age -> DEXA ordering, a BMD toggle, at least
two `DEXA Done!` markers, `Bone Age Done!`, Bone Age PDF navigation evidence,
and no obvious task/gender/duplicate-instance/processing errors.

## If Something Fails

- Hotkey conflict: check `config.json["hotkeys"]` and active window title.
- DEXA mode not detected: rerun `ROI Calibration > RIS OCR ROI` and inspect RIS
  ROI OCR text.
- DEXA values missing: rerun the relevant BMD, Whole Body, or Calcium ROI
  calibration on the PACS monitor.
- Paste goes to the wrong field: rerun `ROI Calibration > RIS Paste Focus`.
- Bone Age wrong page: check `bookmark_map.json` target and PDF-XChange focus.
- Paste failure: increase `paste_timing` delays before changing key simulation.
- Model load failure on offline machine: preload or bundle HuggingFace cache
  because `BoneAgeAIEngine` uses local-only model loading.

## Packaging Smoke Check

Use an onedir build, not onefile:

```powershell
Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
& "C:\Users\xray\AppData\Local\Python\bin\python.exe" -m PyInstaller ".\Radiology_Auto_Reporter.spec"
```

Before deploy, confirm the release folder contains:

- `Radiology_Auto_Reporter.exe`
- `bookmark_map.json`
- `ref_img.png`
- editable external `config.json` in the runtime directory
- local HuggingFace cache available for Bone Age model loading
