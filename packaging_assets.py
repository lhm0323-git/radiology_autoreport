from pathlib import Path


REQUIRED_RUNTIME_FILES = [
    "main.py",
    "config_manager.py",
    "settings_ui.py",
    "platform_routing.py",
    "parser.py",
    "single_instance.py",
    "workstation_log_check.py",
    "preflight_check.py",
    "capture.py",
    "ocr_engine.py",
    "output.py",
    "ai_engine.py",
    "hf_modeling.py",
    "bookmark_map.json",
    "ref_img.png",
    "requirements.txt",
    "Radiology_Auto_Reporter.spec",
    "VERIFICATION_MATRIX.md",
    "verify_unified.py",
    "modules/base.py",
    "modules/dexa.py",
    "modules/bone_age.py",
]

REQUIRED_SPEC_TOKENS = [
    "bookmark_map.json",
    "ref_img.png",
    "rapidocr_onnxruntime",
    "onnxruntime",
    "torch",
    "transformers",
    "timm",
    "Radiology_Auto_Reporter",
    "COLLECT",
]

REQUIRED_CONFIG_KEYS = [
    "bone_age_atlas_path",
    "bone_age_viewer_path",
    "bone_age_bias_offset_months",
    "hotkeys",
    "monitors",
    "auto_detect",
    "paste_timing",
    "ocr_performance",
]

REQUIRED_HOTKEY_KEYS = [
    "start_scan",
    "toggle_bmd",
    "force_male",
    "force_female",
]

REQUIRED_MONITOR_KEYS = [
    "dexa_wb",
    "dexa_bmd",
    "dexa_calcium",
    "bone_age",
]


def validate_packaging_inputs(base_dir, config):
    base = Path(base_dir)
    missing_files = [name for name in REQUIRED_RUNTIME_FILES if not (base / name).exists()]
    missing_config = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    missing_hotkeys = [key for key in REQUIRED_HOTKEY_KEYS if key not in config.get("hotkeys", {})]
    missing_monitors = [key for key in REQUIRED_MONITOR_KEYS if key not in config.get("monitors", {})]

    spec_path = base / "Radiology_Auto_Reporter.spec"
    if spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8")
        missing_spec_tokens = [token for token in REQUIRED_SPEC_TOKENS if token not in spec_text]
    else:
        missing_spec_tokens = REQUIRED_SPEC_TOKENS[:]

    return {
        "ok": not (
            missing_files
            or missing_config
            or missing_hotkeys
            or missing_monitors
            or missing_spec_tokens
        ),
        "missing_files": missing_files,
        "missing_config": missing_config,
        "missing_hotkeys": missing_hotkeys,
        "missing_monitors": missing_monitors,
        "missing_spec_tokens": missing_spec_tokens,
    }
