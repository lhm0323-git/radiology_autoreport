import unittest

from modules.dexa import DexaModule
from modules.base import ModuleContext


def box(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


class FakeOcr:
    def __init__(self, patient_result=None, results_result=None):
        self.patient_result = patient_result or []
        self.results_result = results_result or []
        self.calls = []

    def extract_text(self, image):
        self.calls.append(image)
        if image == "patient":
            return self.patient_result
        return self.results_result


class TestDexaModuleIntegration(unittest.TestCase):
    def test_calcium_mode_uses_shared_services_and_patient_ocr(self):
        import modules.dexa as dexa_module

        captured = {}

        def fake_capture(monitor_idx, config, mode=None):
            captured["monitor_idx"] = monitor_idx
            captured["mode"] = mode
            return "patient", "results"

        calcium_ocr = [
            [box(0, 0, 640, 20), "Artery Lesions Volume Equiv Mass Score", 0.95],
            [box(0, 30, 640, 50), "L.MAIN 0 0.0 0.00 0.0", 0.95],
            [box(0, 60, 640, 80), "LAD 1 5.2 0.95 4.5", 0.95],
            [box(0, 90, 640, 110), "LCX 0 0.0 0.00 0.0", 0.95],
            [box(0, 120, 640, 140), "RCA 0 0.0 0.00 0.0", 0.95],
            [box(0, 180, 640, 200), "Total 1 5.2 0.95 4.5", 0.95],
        ]
        patient_ocr = [[box(0, 0, 80, 20), "057Y M", 0.95]]
        fake_ocr = FakeOcr(patient_result=patient_ocr, results_result=calcium_ocr)
        pasted = []

        original_capture = dexa_module.capture_screen_rois
        try:
            dexa_module.capture_screen_rois = fake_capture
            result = DexaModule().run(
                "dexa",
                {"mode": "calcium", "monitor_idx": 2, "is_manual": False},
                ModuleContext(
                    config={},
                    ocr=fake_ocr,
                    paste=lambda text, config: pasted.append(text),
                ),
            )
        finally:
            dexa_module.capture_screen_rois = original_capture

        self.assertEqual(captured, {"monitor_idx": 2, "mode": "calcium"})
        self.assertEqual(fake_ocr.calls[:2], ["patient", "results"])
        self.assertIn("Agatston Score (Calcium Score)", pasted[0])
        self.assertEqual(result.module_id, "dexa")
        self.assertEqual(result.metadata["mode"], "calcium")


if __name__ == "__main__":
    unittest.main()
