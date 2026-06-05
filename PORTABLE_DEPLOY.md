# Portable Deployment

Target environment: a simple Windows 10/11 workstation with no Python or
development tools installed.

## Build Package

From the build workstation:

```powershell
Set-Location "D:\Users\xray\.gemini\antigravity\scratch\radiology_auto_reporter"
& "C:\Users\xray\AppData\Local\Python\bin\python.exe" ".\package_portable.py" `
  --atlas "D:\download\Atlas_of_Hand_Bone_Age.pdf" `
  --viewer-dir "D:\programs\PDF-XChange Viewer_2.5.311"
```

Output:

```text
dist\Radiology_Auto_Reporter\
```

Copy the whole `dist\Radiology_Auto_Reporter` folder to the target workstation.

## Portable Folder Contents

Required:

- `Radiology_Auto_Reporter.exe`
- `_internal\` PyInstaller runtime files
- `config.json`
- `bookmark_map.json`
- `ref_img.png`
- `hf_cache\hub\models--ianpan--bone-age-crop`
- `hf_cache\hub\models--ianpan--bone-age`
- `README_DEPLOY.txt`

Recommended for Bone Age PDF navigation:

- `assets\Atlas_of_Hand_Bone_Age.pdf`
- `tools\PDF-XChange Viewer_2.5.311\PDFXCview.exe`

`config.json` can use relative paths, for example:

```json
{
  "bone_age_atlas_path": "assets\\Atlas_of_Hand_Bone_Age.pdf",
  "bone_age_viewer_path": "tools\\PDF-XChange Viewer_2.5.311\\PDFXCview.exe"
}
```

## Target Workstation Setup

1. Copy the portable folder to a local path, for example:
   `D:\Radiology_Auto_Reporter`.
2. Run `Radiology_Auto_Reporter.exe`.
3. Use the tray menu `ROI Calibration` on that workstation:
   - RIS OCR ROI
   - RIS Paste Focus
   - BMD ROI
   - Whole Body ROI
   - Calcium ROI
   - Bone Age Hand ROI
4. Use `Reload Config` or restart the app.
5. Verify:
   - `Alt+O` routes Whole Body, BMD, and Calcium correctly.
   - `Shift+2` toggles the last BMD report T/Z mode.
   - `Shift+B` and `Shift+G` run Bone Age with manual gender.
   - PDF atlas jumps to the expected page.

## Expected Performance

- DEXA/Calcium: usually a few seconds after OCR warm-up.
- Bone Age first use: model load can take around 10-15 seconds.
- Bone Age subsequent use: usually around 1-2 seconds after model load.

## Offline Notes

Bone Age uses `local_files_only=True`. It will not download model files on the
target workstation. The portable package must include `hf_cache\hub`.

If Bone Age model loading fails, confirm the portable folder contains both HF
model cache directories listed above.
