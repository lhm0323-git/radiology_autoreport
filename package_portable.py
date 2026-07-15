import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import preflight_check


APP_NAME = "Radiology_Auto_Reporter"


def _require_build_imports():
    missing = [name for name in ("torch", "torchvision", "transformers", "timm") if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError(f"Build environment is missing Bone Age AI dependencies: {', '.join(missing)}")


def _copytree_replace(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _copy_hf_cache(base_dir, dist_dir):
    cache_root = dist_dir / "hf_cache" / "hub"
    cache_root.mkdir(parents=True, exist_ok=True)
    copied = []

    for model_id in preflight_check.REQUIRED_HF_MODELS:
        model_dir_name = preflight_check._hf_model_cache_name(model_id)
        source = None
        for root in preflight_check._hf_cache_roots():
            candidate = root / model_dir_name
            if candidate.exists():
                source = candidate
                break
        if source is None:
            raise RuntimeError(f"Missing local HuggingFace cache for {model_id}")
        _copytree_replace(source, cache_root / model_dir_name)
        copied.append(model_id)

    return copied


def _copy_optional_assets(dist_dir, config, atlas_path=None, viewer_dir=None):
    assets_dir = dist_dir / "assets"
    tools_dir = dist_dir / "tools"

    if atlas_path:
        atlas_src = Path(atlas_path)
        if not atlas_src.exists():
            raise RuntimeError(f"Atlas PDF not found: {atlas_src}")
        assets_dir.mkdir(parents=True, exist_ok=True)
        atlas_dst = assets_dir / atlas_src.name
        shutil.copy2(atlas_src, atlas_dst)
        config["bone_age_atlas_path"] = str(Path("assets") / atlas_dst.name)

    if viewer_dir:
        viewer_src = Path(viewer_dir)
        if not viewer_src.exists():
            raise RuntimeError(f"PDF-XChange Viewer directory not found: {viewer_src}")
        viewer_dst = tools_dir / viewer_src.name
        _copytree_replace(viewer_src, viewer_dst)
        exe_candidates = list(viewer_dst.rglob("PDFXCview.exe"))
        if not exe_candidates:
            raise RuntimeError(f"PDFXCview.exe not found under copied viewer directory: {viewer_dst}")
        config["bone_age_viewer_path"] = str(exe_candidates[0].relative_to(dist_dir))


def _copy_root_runtime_assets(base_dir, dist_dir):
    for name in ("bookmark_map.json", "ref_img.png"):
        source = base_dir / name
        if not source.exists():
            raise RuntimeError(f"Required runtime asset missing: {source}")
        shutil.copy2(source, dist_dir / name)


def _write_deploy_readme(dist_dir):
    text = """Radiology Auto-Reporter Portable Package

Target: Windows 10/11 workstation without Python.

Run:
1. Open this folder.
2. Double-click Radiology_Auto_Reporter.exe.
3. From the tray icon, run ROI Calibration for the workstation:
   - RIS OCR ROI
   - RIS Paste Focus
   - BMD ROI
   - Whole Body ROI
   - Calcium ROI
   - Bone Age Hand ROI
4. Use Reload Config after calibration, or restart the app.

Important files:
- config.json: hotkeys, monitor mapping, ROI, report templates, atlas/viewer paths.
- hf_cache/hub: bundled offline Bone Age AI model cache.
- bookmark_map.json and ref_img.png: runtime assets required by Bone Age.

Hotkeys:
- Alt+O: route DEXA/Calcium from RIS title
- Shift+2: toggle last BMD T/Z mode
- Shift+B: Bone Age male
- Shift+G: Bone Age female
- Scroll Lock: suspend/resume hotkeys

If Bone Age fails on an offline workstation, confirm hf_cache/hub contains:
- models--ianpan--bone-age-crop
- models--ianpan--bone-age
"""
    (dist_dir / "README_DEPLOY.txt").write_text(text, encoding="utf-8")


def build_portable(args):
    base_dir = Path(__file__).resolve().parent
    spec_path = base_dir / "Radiology_Auto_Reporter.spec"
    dist_dir = base_dir / "dist" / APP_NAME

    if not args.skip_build:
        _require_build_imports()
        subprocess.run([sys.executable, "-m", "PyInstaller", "-y", str(spec_path)], cwd=base_dir, check=True)

    if not dist_dir.exists():
        raise RuntimeError(f"PyInstaller output not found: {dist_dir}")

    config = json.loads((base_dir / "config.json").read_text(encoding="utf-8"))
    _copy_root_runtime_assets(base_dir, dist_dir)
    _copy_optional_assets(dist_dir, config, args.atlas, args.viewer_dir)
    (dist_dir / "config.json").write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")

    copied_models = _copy_hf_cache(base_dir, dist_dir)
    _write_deploy_readme(dist_dir)

    print(f"Portable package ready: {dist_dir}")
    print("Bundled HF models:")
    for model in copied_models:
        print(f"  - {model}")
    print("Run on target workstation: Radiology_Auto_Reporter.exe")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build portable Radiology Auto-Reporter onedir package.")
    parser.add_argument("--skip-build", action="store_true", help="Reuse existing dist/Radiology_Auto_Reporter.")
    parser.add_argument("--atlas", help="Optional Atlas_of_Hand_Bone_Age.pdf path to copy into assets/.")
    parser.add_argument("--viewer-dir", help="Optional portable PDF-XChange Viewer directory to copy into tools/.")
    args = parser.parse_args(argv)
    build_portable(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
