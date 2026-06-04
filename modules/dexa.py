import time

from capture import capture_screen_rois
import parser as p

from .base import ModuleContext, ModuleResult


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

        needs_patient_ocr = mode != "calcium"
        if needs_patient_ocr:
            patient_ocr_start = time.perf_counter()
            patient_res = context.ocr.extract_text(patient_img)
            context.notify(f"[DEXA] OCR Patient Info took {time.perf_counter() - patient_ocr_start:.2f}s")
        else:
            patient_res = []
            context.notify("[DEXA] OCR Patient Info skipped for Calcium mode")

        results_ocr_start = time.perf_counter()
        results_res = context.ocr.extract_text(results_img)
        context.notify(f"[DEXA] OCR Results took {time.perf_counter() - results_ocr_start:.2f}s")

        parse_start = time.perf_counter()
        patient_info = p.parse_patient_info(patient_res)

        if mode == "whole_body":
            results_data = p.parse_whole_body(results_res)
        elif mode == "calcium":
            results_data = p.parse_calcium_scores(results_res)
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
