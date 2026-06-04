import json
import math
import os
import re
import time

from capture import capture_bone_age_roi

from .base import ModuleContext, ModuleResult


DEFAULT_BIAS_OFFSET_MONTHS = -5.0


def apply_calibration_offset(pred_months: float, offset_months: float = DEFAULT_BIAS_OFFSET_MONTHS) -> float:
    return max(0.0, float(pred_months) + float(offset_months))


def _format_year(value: float) -> str:
    return f"{int(value)}" if float(value).is_integer() else f"{value:g}"


def resolve_gender_from_ocr_texts(texts):
    tokens = []
    joined_parts = []
    for text in texts:
        if not isinstance(text, str):
            continue
        upper = text.strip().upper()
        if not upper:
            continue
        joined_parts.append(upper)
        tokens.extend(re.findall(r"[A-Z]+|[0-9]+", upper))

    joined = " ".join(joined_parts)
    compact = re.sub(r"\s+", "", joined)

    if re.search(r"\bSEX\s*[:：]\s*F\b", joined) or "SEX:F" in compact:
        return True
    if re.search(r"\bSEX\s*[:：]\s*M\b", joined) or "SEX:M" in compact:
        return False
    if "FEMALE" in tokens:
        return True
    if "MALE" in tokens:
        return False
    if any(token == "F" for token in tokens):
        return True
    if any(token == "M" for token in tokens):
        return False
    return None


def format_bone_age(
    pred_months: float,
    is_female: bool,
    offset_months: float = DEFAULT_BIAS_OFFSET_MONTHS,
) -> dict:
    months = apply_calibration_offset(pred_months, offset_months)
    years = months / 12.0

    if years >= 6:
        lower_year = math.floor(years)
        upper_year = lower_year + 1
        report_age = f"{lower_year}-{upper_year} year"
        target_age_str = f"{lower_year}-year-old"
    elif years >= 2:
        lower = math.floor(years * 2) / 2
        upper = lower + 0.5
        report_age = f"{_format_year(lower)}-{_format_year(upper)} years"

        closest = round(years * 2) / 2
        target_age_str = f"{_format_year(closest)}-year-old"
    else:
        lower_mo = math.floor(months / 2) * 2
        upper_mo = lower_mo + 2
        report_age = f"{int(lower_mo)}-{int(upper_mo)} months"

        closest_mo = round(months / 2) * 2
        if closest_mo < 8:
            closest_mo = 8
        if closest_mo >= 22:
            target_age_str = "2-year-old"
        else:
            target_age_str = f"{int(closest_mo)}-month-old"

    gender_str = "girl" if is_female else "boy"
    bookmark_target = f"{target_age_str} {gender_str}"
    return {
        "raw_months": float(pred_months),
        "offset_months": float(offset_months),
        "calibrated_months": months,
        "report_age": report_age,
        "target_age": target_age_str,
        "gender": gender_str,
        "bookmark_target": bookmark_target,
    }


def load_bookmark_map(base_dir: str) -> dict:
    bookmark_map_path = os.path.join(base_dir, "bookmark_map.json")
    with open(bookmark_map_path, "r", encoding="utf-8") as f:
        return json.load(f)


class BoneAgeModule:
    module_id = "bone_age"
    task_types = {"bone_age"}

    def __init__(self, ai_engine, base_dir: str | None = None):
        self.ai_engine = ai_engine
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.task_types

    def run(self, task_type: str, force_gender: str | None, context: ModuleContext) -> ModuleResult:
        start_time = time.perf_counter()
        m_idx = context.config.get("monitors", {}).get("bone_age", 2)
        pacs_img = capture_bone_age_roi(m_idx, context.config)

        if pacs_img is None:
            raise RuntimeError("Failed to capture PACS monitor.")

        is_female = self._resolve_gender(pacs_img, force_gender, context)
        predict_start = time.perf_counter()
        pred_months = self.ai_engine.predict(pacs_img, is_female)
        context.notify(f"[BoneAge] AI predict took {time.perf_counter() - predict_start:.2f}s")

        offset_months = context.config.get("bone_age_bias_offset_months", DEFAULT_BIAS_OFFSET_MONTHS)
        age_info = format_bone_age(pred_months, is_female, offset_months)

        try:
            bookmarks = load_bookmark_map(self.base_dir)
        except Exception as exc:
            context.notify(f"Failed to load bookmark map: {exc}")
            bookmarks = {}

        target_page = bookmarks.get(age_info["bookmark_target"], 1)
        if target_page == 1:
            context.notify(f"Warning: bookmark target not found: {age_info['bookmark_target']}")
        report_text = self._render_report(age_info["report_age"], context.config)

        context.notify(
            "Predicted Age: "
            f"raw={age_info['raw_months']:.2f} months, "
            f"offset={age_info['offset_months']:+.2f} months, "
            f"calibrated={age_info['calibrated_months']:.2f} months, "
            f"report={age_info['report_age']}, target={age_info['bookmark_target']}. "
            "Pasting report..."
        )
        context.paste(report_text, context.config)
        context.notify(f"[BoneAge] Total module run took {time.perf_counter() - start_time:.2f}s")
        return ModuleResult(
            module_id=self.module_id,
            report_text=report_text,
            metadata={
                "predicted_months": pred_months,
                "is_female": is_female,
                "target_page": target_page,
                **age_info,
            },
            actions=[
                {"type": "open_reference_pdf", "page": target_page},
                {"type": "paste_report"},
            ],
        )

    def _resolve_gender(self, pacs_img, force_gender: str | None, context: ModuleContext) -> bool:
        if force_gender == "M":
            context.notify("Gender forced to: Male")
            return False
        if force_gender == "F":
            context.notify("Gender forced to: Female")
            return True

        context.notify("Gender was not specified. Use shift+b for male or shift+g for female.")
        raise RuntimeError("Bone Age requires explicit gender override.")

    def _resolve_gender_from_ocr(self, pacs_img, context: ModuleContext):
        context.notify("Extracting Gender from PACS image...")
        h, w = pacs_img.shape[:2]
        ocr_img = pacs_img[0:int(h * 0.35), 0:int(w * 0.45)]
        res = context.ocr.extract_text(ocr_img)
        texts = [item[1] for item in res if len(item) > 1] if res else []
        return resolve_gender_from_ocr_texts(texts)

    def _render_report(self, report_age: str, config: dict) -> str:
        template = config.get(
            "bone_age_template",
            "According The Radiographic Atlas of Skeletal Development of  The Hand and Wrist.\n"
            "The skeletal age is about {age_range} old.",
        )
        report_text = template.replace("{age_range}", report_age)
        return report_text.replace("{years} years", report_age).replace("{years}", report_age)
