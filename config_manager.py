import json
import os
import sys


if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(application_path, "config.json")


WHOLE_BODY_TEMPLATE = (
    "Body Composition Assessment\n"
    "\n"
    "1.Total body fat percentage: {fat_percent}%\n"
    "\n"
    "2.Estimated visceral adipose tissue (VAT area): {vat_area} cm2\n"
    "Result: {vat_result}\n"
    "Reference:Normal:<100;Increased:100~160;High:>=160\n"
    "\n"
    "3.Appendicular Lean/Height2 (muscle mass) index: {lean_index} kg/m2\n"
    "Result: {lean_result}\n"
    "Reference:AWGS 2019 (Asian Working Group for Sarcopenia)\n"
    "Male:Low lean mass:<7.0 kg/m2;normal:>=7.0 kg/m2\n"
    "Female:Low lean mass:<5.4 kg/m2;normal:>=5.4kg/m2\n"
    "\n"
    "4.Android/Gynoid Ratio: {ag_ratio}\n"
    "Result: {ag_result}\n"
    "Reference:>=1:Apple-shape; <1: Pear-shape"
)

BMD_TEMPLATE = "BMD Assessment\nClassification: {classification}\n{score_type}: {score_value}"

CALCIUM_TEMPLATE = (
    "Agatston Score (Calcium Score)\n"
    "------------------------------\n"
    "L.MAIN:  {LM}\n"
    "LAD   :  {LAD}\n"
    "LCX   :  {CX}\n"
    "RCA   :  {RCA}\n"
    "------------------------------\n"
    "Total :  {Total}\n"
    "Total Calcium Score was {Total}"
)


def default_config():
    return {
        "hotkeys": {
            "start_scan": "alt+o",
            "toggle_bmd": "shift+2",
            "force_male": "shift+b",
            "force_female": "shift+g",
            "suspend": "scroll_lock",
            "active_window_keywords": ["ris", "pacs", "impax", "屏基", "醫療資訊系統"],
        },
        "monitors": {
            "dexa_wb": 1,
            "dexa_bmd": 2,
            "dexa_calcium": 2,
            "bone_age": 2,
        },
        "roi_patient_info": {
            "left_pct": 0.005,
            "top_pct": 0.05,
            "width_pct": 0.35,
            "height_pct": 0.15,
        },
        "roi_results_summary": {
            "left_pct": 0.65,
            "top_pct": 0.30,
            "width_pct": 0.30,
            "height_pct": 0.25,
        },
        "roi_patient_id": {
            "left_pct": 0.0104,
            "top_pct": 0.1972,
            "width_pct": 0.9036,
            "height_pct": 0.1213,
        },
        "roi_bmd": {
            "patient_info": {
                "left_pct": 0.0091,
                "top_pct": 0.2793,
                "width_pct": 0.2624,
                "height_pct": 0.1899,
            },
            "results": {
                "left_pct": 0.3132,
                "top_pct": 0.5332,
                "width_pct": 0.6816,
                "height_pct": 0.2495,
            },
        },
        "roi_wb": {
            "patient_info": {
                "left_pct": 0.0026,
                "top_pct": 0.2397,
                "width_pct": 0.2917,
                "height_pct": 0.127,
            },
            "results": {
                "left_pct": 0.5169,
                "top_pct": 0.6851,
                "width_pct": 0.3932,
                "height_pct": 0.2617,
            },
        },
        "roi_calcium": {
            "patient_info": {
                "left_pct": 0.0013,
                "top_pct": 0.5859,
                "width_pct": 0.1081,
                "height_pct": 0.0498,
            },
            "results": {
                "left_pct": 0.0195,
                "top_pct": 0.6709,
                "width_pct": 0.4609,
                "height_pct": 0.1641,
            },
        },
        "roi_bone_age": {
            "left_pct": 0.0,
            "top_pct": 0.0,
            "width_pct": 1.0,
            "height_pct": 0.8,
        },
        "whole_body_template": WHOLE_BODY_TEMPLATE,
        "bmd_template": BMD_TEMPLATE,
        "calcium_template": CALCIUM_TEMPLATE,
        "templates": {
            "whole_body": WHOLE_BODY_TEMPLATE,
            "bmd": BMD_TEMPLATE,
            "calcium": CALCIUM_TEMPLATE,
        },
        "bone_age_template": (
            "According The Radiographic Atlas of Skeletal Development of  The Hand and Wrist.\n"
            "The skeletal age is about {age_range} old."
        ),
        "bone_age_bias_offset_months": -5.0,
        "bone_age_atlas_path": r"D:\download\Atlas_of_Hand_Bone_Age.pdf",
        "bone_age_viewer_path": r"D:\programs\PDF-XChange Viewer_2.5.311\PDFXCview.exe",
        "auto_detect": {
            "enabled": False,
            "monitor_idx": 3,
            "ris_fallback_enabled": False,
            "poll_interval_seconds": 5.0,
            "delay_after_detect": 2.0,
            "roi": {
                "left_pct": 0.0,
                "top_pct": 0.0,
                "width_pct": 1.0,
                "height_pct": 0.5,
            },
        },
        "click_before_paste": {
            "enabled": True,
            "monitor_idx": 3,
            "x_pct": 0.7547,
            "y_pct": 0.4981,
        },
        "paste_timing": {
            "modifier_release_delay": 0.02,
            "focus_click_delay": 0.15,
            "key_hold_delay": 0.03,
            "after_select_delay": 0.05,
            "after_clear_delay": 0.05,
            "clipboard_retry_delay": 0.03,
        },
        "ocr_performance": {
            "threads": 2,
            "warm_up_on_start": True,
        },
    }


def migrate_config(config):
    defaults = default_config()

    config.setdefault("hotkeys", {})
    config["hotkeys"].pop("dexa_wb", None)
    config["hotkeys"].pop("dexa_bmd", None)
    config["hotkeys"].pop("bone_age", None)
    config["hotkeys"].pop("bone_age_trigger", None)
    for key, value in defaults["hotkeys"].items():
        config["hotkeys"].setdefault(key, value)
    config["hotkeys"]["active_window_keywords"] = defaults["hotkeys"]["active_window_keywords"]

    config.setdefault("monitors", {})
    for key, value in defaults["monitors"].items():
        if key == "dexa_calcium":
            config["monitors"].setdefault(key, config["monitors"].get("dexa_bmd", value))
        else:
            config["monitors"].setdefault(key, value)

    for key in (
        "roi_patient_info",
        "roi_results_summary",
        "roi_patient_id",
        "roi_bmd",
        "roi_wb",
        "roi_calcium",
        "roi_bone_age",
        "auto_detect",
    ):
        config.setdefault(key, defaults[key])
    if "manual_trigger_migration_20260604" not in config:
        config.setdefault("auto_detect", {})
        config["auto_detect"]["enabled"] = False
        config["manual_trigger_migration_20260604"] = True

    legacy_whole_body_prefix = "Body Composition Assessment\n\n1.Total body fat percentage: {fat_percent}%\nResult: {fat_result}"
    if config.get("whole_body_template", "").startswith(legacy_whole_body_prefix):
        config["whole_body_template"] = defaults["whole_body_template"]

    config.setdefault("whole_body_template", defaults["whole_body_template"])
    config.setdefault("bmd_template", defaults["bmd_template"])
    config.setdefault("calcium_template", defaults["calcium_template"])
    config.setdefault("templates", {})
    if config["templates"].get("whole_body", "").startswith(legacy_whole_body_prefix):
        config["templates"]["whole_body"] = config["whole_body_template"]
    config["templates"].setdefault("whole_body", config.get("whole_body_template", WHOLE_BODY_TEMPLATE))
    config["templates"].setdefault("bmd", config.get("bmd_template", BMD_TEMPLATE))
    config["templates"].setdefault("calcium", config.get("calcium_template", CALCIUM_TEMPLATE))

    for key in (
        "bone_age_template",
        "calcium_template",
        "bone_age_bias_offset_months",
        "bone_age_atlas_path",
        "bone_age_viewer_path",
        "paste_timing",
        "ocr_performance",
        "click_before_paste",
    ):
        config.setdefault(key, defaults[key])

    return config


def load_config():
    if not os.path.exists(CONFIG_PATH):
        config = default_config()
        save_config(config)
        return config

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return migrate_config(json.load(f))


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
