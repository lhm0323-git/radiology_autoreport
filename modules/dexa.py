import re
import time

import cv2

from capture import capture_screen_rois
import parser as p

from .base import ModuleContext, ModuleResult


def _ocr_texts(ocr_results):
    return [str(item[1]) for item in ocr_results or [] if len(item) > 1]


def _enhance_patient_roi(image):
    if not hasattr(image, "shape"):
        return image
    scaled = cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def _infer_sex_from_age_row(image, ocr_results):
    if not hasattr(image, "shape"):
        return None
    h, w = image.shape[:2]
    age_box = None
    for item in ocr_results or []:
        if len(item) < 2:
            continue
        text = str(item[1]).lower().replace("o", "0")
        if not re.search(r"0*\d{1,3}\s*y", text):
            continue
        box = item[0]
        if max(point[0] for point in box) <= w and max(point[1] for point in box) <= h:
            age_box = box
            break
    if age_box is None:
        return None

    x0 = max(0, int(min(point[0] for point in age_box)) - 8)
    x1 = min(w, x0 + 70)
    y0 = max(0, int(max(point[1] for point in age_box)))
    y1 = min(h, y0 + max(28, int((max(point[1] for point in age_box) - min(point[1] for point in age_box)) * 2.2)))
    crop = image[y0:y1, x0:x1]
    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    parts = []
    for idx in range(1, count):
        x, y, bw, bh, area = stats[idx]
        if 4 <= bw <= 45 and 8 <= bh <= 45 and area >= 15:
            parts.append((x, y, bw, bh))
    if not parts:
        return None

    x0 = min(part[0] for part in parts)
    y0 = min(part[1] for part in parts)
    x1 = max(part[0] + part[2] for part in parts)
    y1 = max(part[1] + part[3] for part in parts)
    glyph = binary[y0:y1, x0:x1]
    if glyph.size == 0:
        return None
    glyph = cv2.resize(glyph, (32, 32), interpolation=cv2.INTER_NEAREST)
    lower_right = cv2.countNonZero(glyph[17:32, 16:32])
    return "Male" if lower_right >= 8 else "Female"


class DexaModule:
    module_id = "dexa"
    task_types = {"dexa", "dexa_wb", "dexa_bmd", "dexa_calcium", "dexa_toggle"}

    def __init__(self):
        self.last_patient_info = None
        self.last_results = None
        self.last_exam_type = None
        self.last_forced_toggle = False

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.task_types

    def run(self, task_type: str, param, context: ModuleContext) -> ModuleResult:
        if task_type == "dexa_toggle":
            return self._toggle_last_report(context)

        total_start = time.perf_counter()
        mode, monitor_idx, is_manual = self._resolve_task(task_type, param, context.config)
        capture_start = time.perf_counter()
        patient_img, results_img = capture_screen_rois(monitor_idx, context.config, mode=mode)
        context.notify(f"[DEXA] Capture ROIs took {time.perf_counter() - capture_start:.2f}s")
        if patient_img is None or results_img is None:
            raise RuntimeError(f"DEXA capture failed for mode={mode}.")

        patient_ocr_start = time.perf_counter()
        patient_res = context.ocr.extract_text(patient_img)
        context.notify(f"[DEXA] OCR Patient Info took {time.perf_counter() - patient_ocr_start:.2f}s")

        results_ocr_start = time.perf_counter()
        results_res = context.ocr.extract_text(results_img)
        context.notify(f"[DEXA] OCR Results took {time.perf_counter() - results_ocr_start:.2f}s")

        parse_start = time.perf_counter()
        patient_info = p.parse_patient_info(patient_res)
        if mode == "calcium" and (patient_info.get("Age") is None or patient_info.get("Sex") is None):
            enhanced_res = context.ocr.extract_text(_enhance_patient_roi(patient_img))
            patient_res = (patient_res or []) + (enhanced_res or [])
            patient_info = p.parse_patient_info(patient_res)
            if patient_info.get("Age") is not None and patient_info.get("Sex") is None:
                inferred_sex = _infer_sex_from_age_row(patient_img, patient_res)
                if inferred_sex:
                    patient_info["Sex"] = inferred_sex
                    context.notify(f"[Calcium] Sex inferred from patient ROI image: {inferred_sex}")
            if patient_info.get("Age") is None or patient_info.get("Sex") is None:
                cv2.imwrite("calcium_patient_roi_debug.png", patient_img)
                context.notify(f"[Calcium] Saved patient ROI debug image: calcium_patient_roi_debug.png ({patient_img.shape[1]}x{patient_img.shape[0]})")
                context.notify(f"[Calcium] Patient OCR text: {_ocr_texts(patient_res)}")
                context.notify(f"[Calcium] Parsed patient info: {patient_info}")

        if mode == "whole_body":
            results_data = p.parse_whole_body(results_res)
        elif mode == "calcium":
            results_data = p.parse_calcium_scores(results_res)
            p.add_mesa_percentile(patient_info, results_data, context.config.get("mesa_race", "chinese"))
        else:
            results_data = p.parse_bmd_v2(results_res)

        self.last_patient_info = patient_info
        self.last_results = results_data
        self.last_exam_type = mode

        if is_manual and mode == "bmd":
            self.last_forced_toggle = not self.last_forced_toggle
        else:
            self.last_forced_toggle = False

        report_text, final_data = p.apply_clinical_logic(
            patient_info,
            mode,
            results_data,
            context.config,
            force_toggle=self.last_forced_toggle,
        )
        context.notify(f"[DEXA] Parse/report took {time.perf_counter() - parse_start:.2f}s")
        if not report_text:
            raise RuntimeError(f"DEXA report generation failed for mode={mode}.")
        if not results_data.get("is_valid", True):
            raise RuntimeError(f"No valid DEXA data patterns found for mode={mode}.")

        paste_start = time.perf_counter()
        context.paste(report_text, context.config)
        context.notify(f"[DEXA] Paste took {time.perf_counter() - paste_start:.2f}s")
        context.notify(f"[DEXA] Total module run took {time.perf_counter() - total_start:.2f}s")
        return ModuleResult(
            module_id=self.module_id,
            report_text=report_text,
            metadata={
                "patient_info": patient_info,
                "mode": mode,
                "results_data": final_data,
                "monitor_idx": monitor_idx,
            },
            actions=[{"type": "paste_report"}],
        )

    def _resolve_task(self, task_type, param, config):
        if isinstance(param, dict):
            return (
                param.get("mode", "bmd"),
                param.get("monitor_idx", 2),
                param.get("is_manual", False),
            )

        if task_type == "dexa_wb":
            return "whole_body", param, True
        if task_type == "dexa_calcium":
            return "calcium", param, False
        return "bmd", param, task_type == "dexa_bmd"

    def _toggle_last_report(self, context):
        if not self.last_results or self.last_exam_type != "bmd":
            context.notify("No valid BMD report to toggle.")
            return ModuleResult(
                module_id=self.module_id,
                report_text="",
                metadata={"mode": "bmd", "toggled": False},
            )

        self.last_forced_toggle = not self.last_forced_toggle
        report_text, final_data = p.apply_clinical_logic(
            self.last_patient_info,
            self.last_exam_type,
            self.last_results,
            context.config,
            force_toggle=self.last_forced_toggle,
        )
        context.paste(report_text, context.config)
        return ModuleResult(
            module_id=self.module_id,
            report_text=report_text,
            metadata={"mode": "bmd", "results_data": final_data, "toggled": True},
            actions=[{"type": "paste_report"}],
        )
