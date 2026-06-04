import unittest

import numpy as np

import config_manager
from modules.base import ModuleContext
from modules.bone_age import BoneAgeModule
from modules.dexa import DexaModule


def box(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


class SessionOcr:
    def __init__(self):
        self.calls = []

    def extract_text(self, image):
        self.calls.append(image)
        if image == "dexa_patient":
            return [
                [box(0, 0, 100, 20), "Sex: Female", 0.95],
                [box(0, 30, 100, 50), "Age: 45", 0.95],
            ]
        if image == "dexa_bmd_results":
            return [
                [box(0, 0, 80, 10), "Region", 0.95],
                [box(300, 0, 360, 10), "T-score", 0.95],
                [box(500, 0, 560, 10), "Z-score", 0.95],
                [box(0, 20, 100, 30), "Femoral Neck", 0.95],
                [box(110, 20, 150, 30), "2.38", 0.95],
                [box(180, 20, 220, 30), "4.08", 0.95],
                [box(240, 20, 285, 30), "0.584", 0.95],
                [box(310, 20, 350, 30), "-2.6", 0.95],
                [box(390, 20, 420, 30), "68", 0.95],
                [box(510, 20, 550, 30), "-2.0", 0.95],
                [box(590, 20, 620, 30), "110", 0.95],
            ]
        if image == "dexa_calcium_results":
            return [
                [box(0, 0, 640, 20), "Artery Lesions Volume Equiv Mass Score", 0.95],
                [box(0, 30, 640, 50), "L.MAIN 0 0.0 0.00 0.0", 0.95],
                [box(0, 60, 640, 80), "LAD 1 5.2 0.95 4.5", 0.95],
                [box(0, 90, 640, 110), "LCX 0 0.0 0.00 0.0", 0.95],
                [box(0, 120, 640, 140), "RCA 0 0.0 0.00 0.0", 0.95],
                [box(0, 180, 640, 200), "Total 1 5.2 0.95 4.5", 0.95],
            ]
        return []


class FakeBoneAgeAi:
    def __init__(self):
        self.calls = []

    def predict(self, image, is_female):
        self.calls.append((image.shape, is_female))
        return 29.0


class TestSameSessionQueue(unittest.TestCase):
    def test_dexa_bone_age_dexa_sequence_keeps_module_state_isolated(self):
        import modules.bone_age as bone_age_module
        import modules.dexa as dexa_module

        config = config_manager.default_config()
        config["bone_age_bias_offset_months"] = -5.0
        pasted = []
        notifications = []
        context = ModuleContext(
            config=config,
            ocr=SessionOcr(),
            paste=lambda text, cfg: pasted.append(text),
            notify=notifications.append,
        )
        dexa = DexaModule()
        bone_age = BoneAgeModule(FakeBoneAgeAi())

        def fake_dexa_capture(monitor_idx, cfg, mode=None):
            if mode == "calcium":
                return "dexa_patient", "dexa_calcium_results"
            return "dexa_patient", "dexa_bmd_results"

        def fake_bone_age_capture(monitor_idx, cfg):
            return np.zeros((128, 128, 3), dtype=np.uint8)

        original_dexa_capture = dexa_module.capture_screen_rois
        original_ba_capture = bone_age_module.capture_bone_age_roi
        try:
            dexa_module.capture_screen_rois = fake_dexa_capture
            bone_age_module.capture_bone_age_roi = fake_bone_age_capture

            bmd_result = dexa.run(
                "dexa",
                {"mode": "bmd", "monitor_idx": 2, "is_manual": False},
                context,
            )
            bone_result = bone_age.run("bone_age", "F", context)
            toggle_result = dexa.run("dexa_toggle", None, context)
            calcium_result = dexa.run(
                "dexa",
                {"mode": "calcium", "monitor_idx": 3, "is_manual": False},
                context,
            )
        finally:
            dexa_module.capture_screen_rois = original_dexa_capture
            bone_age_module.capture_bone_age_roi = original_ba_capture

        self.assertEqual(bmd_result.metadata["mode"], "bmd")
        self.assertEqual(bone_result.metadata["target_page"], 76)
        self.assertTrue(toggle_result.metadata["toggled"])
        self.assertEqual(calcium_result.metadata["mode"], "calcium")
        self.assertEqual(len(pasted), 4)
        self.assertIn("lowest Z-score", pasted[0])
        self.assertIn("skeletal age is about 2-2.5 years old", pasted[1])
        self.assertIn("lowest T-score", pasted[2])
        self.assertIn("Agatston Score (Calcium Score)", pasted[3])
        self.assertEqual(dexa.last_exam_type, "calcium")
        self.assertIn("Gender forced to: Female", notifications)


if __name__ == "__main__":
    unittest.main()
