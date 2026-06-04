import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import config_manager
import packaging_assets


REQUIRED_HF_MODELS = [
    "ianpan/bone-age-crop",
    "ianpan/bone-age",
]


@dataclass
class PreflightResult:
    ok: bool
    missing: list[str]
    warnings: list[str]


def _hf_cache_roots(env=None):
    use_default_home = env is None
    env = os.environ if env is None else env
    roots = []
    if env.get("HF_HOME"):
        roots.append(Path(env["HF_HOME"]) / "hub")
    if env.get("TRANSFORMERS_CACHE"):
        roots.append(Path(env["TRANSFORMERS_CACHE"]))
    if env.get("HUGGINGFACE_HUB_CACHE"):
        roots.append(Path(env["HUGGINGFACE_HUB_CACHE"]))
    if env.get("USERPROFILE"):
        roots.append(Path(env["USERPROFILE"]) / ".cache" / "huggingface" / "hub")
    if env.get("XDG_CACHE_HOME"):
        roots.append(Path(env["XDG_CACHE_HOME"]) / "huggingface" / "hub")
    if use_default_home:
        roots.append(Path.home() / ".cache" / "huggingface" / "hub")
    return list(dict.fromkeys(roots))


def _hf_model_cache_name(model_id):
    return "models--" + model_id.replace("/", "--")


def _has_hf_model_cache(model_id, env=None):
    model_dir_name = _hf_model_cache_name(model_id)
    for root in _hf_cache_roots(env):
        model_dir = root / model_dir_name
        if model_dir.exists():
            return True
    return False


def run_preflight(base_dir, config, strict_external=False, env=None):
    base = Path(base_dir)
    missing = []
    warnings = []

    packaging_result = packaging_assets.validate_packaging_inputs(base, config)
    if not packaging_result["ok"]:
        for key, values in packaging_result.items():
            if key != "ok" and values:
                missing.append(f"{key}: {values}")

    for asset_name in ("bookmark_map.json", "ref_img.png"):
        if not (base / asset_name).exists():
            missing.append(asset_name)

    for model_id in REQUIRED_HF_MODELS:
        if not _has_hf_model_cache(model_id, env):
            message = f"local HuggingFace cache missing for {model_id}"
            if strict_external:
                missing.append(message)
            else:
                warnings.append(message)

    external_paths = {
        "bone_age_atlas_path": config.get("bone_age_atlas_path"),
        "bone_age_viewer_path": config.get("bone_age_viewer_path"),
    }
    for key, value in external_paths.items():
        if not value:
            missing.append(key)
            continue
        if not Path(value).exists():
            message = f"{key} not found: {value}"
            if strict_external:
                missing.append(message)
            else:
                warnings.append(message)

    return PreflightResult(ok=not missing, missing=missing, warnings=warnings)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run unified app deployment preflight checks.")
    parser.add_argument("--strict-external", action="store_true", help="Require atlas/PDF viewer/HF cache paths to exist.")
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parent
    config = config_manager.load_config()
    result = run_preflight(base, config, strict_external=args.strict_external)

    if result.warnings:
        print("warnings:")
        for item in result.warnings:
            print(f"  - {item}")
    if result.missing:
        print("missing:")
        for item in result.missing:
            print(f"  - {item}")
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
