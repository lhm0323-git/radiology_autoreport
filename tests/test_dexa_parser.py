import unittest
import parser as p


def box(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


class TestDexaParser(unittest.TestCase):
    def test_bmd_parsing_basic(self):
        ocr_res = [
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

        data = p.parse_bmd_v2(ocr_res)

        self.assertEqual(data["t_score"], -2.6)
        self.assertEqual(data["z_score"], -2.0)
        self.assertTrue(data["has_neck"])

    def test_bmd_pr_peak_reference_is_not_t_score_column(self):
        ocr_res = [
            [box(0, 0, 70, 20), "Region", 0.95],
            [box(80, 0, 160, 20), "Area [cm2]", 0.95],
            [box(170, 0, 250, 20), "BMC [(g)]", 0.95],
            [box(260, 0, 360, 20), "BMD [g/cm2]", 0.95],
            [box(380, 0, 460, 20), "T-score", 0.95],
            [box(470, 0, 650, 20), "PR (Peak Reference)", 0.95],
            [box(660, 0, 740, 20), "Z-score", 0.95],
            [box(750, 0, 900, 20), "AM (Age Matched)", 0.95],
            [box(0, 40, 70, 60), "Neck", 0.95],
            [box(80, 40, 160, 60), "5.81", 0.95],
            [box(170, 40, 250, 60), "4.96", 0.95],
            [box(260, 40, 360, 60), "0.854", 0.95],
            [box(380, 40, 460, 60), "0.0", 0.95],
            [box(470, 40, 650, 60), "101", 0.95],
            [box(660, 40, 740, 60), "1.0", 0.95],
            [box(750, 40, 900, 60), "117", 0.95],
            [box(0, 80, 70, 100), "Total", 0.95],
            [box(80, 80, 160, 100), "54.77", 0.95],
            [box(170, 80, 250, 100), "57.60", 0.95],
            [box(260, 80, 360, 100), "1.052", 0.95],
            [box(380, 80, 460, 100), "0.9", 0.95],
            [box(470, 80, 650, 100), "112", 0.95],
            [box(660, 80, 740, 100), "1.3", 0.95],
            [box(750, 80, 900, 100), "119", 0.95],
            [box(0, 120, 900, 140), "Total BMD CV 1.0%, ACF = 1.021, BCF = 1.002, TH = 6.439", 0.95],
            [box(0, 160, 100, 180), "7.0", 0.95],
        ]

        data = p.parse_bmd_v2(ocr_res)

        self.assertEqual(data["t_score"], 0.0)
        self.assertEqual(data["z_score"], 1.0)
        self.assertTrue(data["has_neck"])

    def test_bmd_missing_t_score_header_does_not_fallback_to_unknown_graph_number(self):
        ocr_res = [
            [box(0, 0, 70, 20), "Region", 0.95],
            [box(80, 0, 160, 20), "Area [cm2]", 0.95],
            [box(170, 0, 250, 20), "BMC [(g)]", 0.95],
            [box(260, 0, 360, 20), "BMD [g/cm2]", 0.95],
            [box(470, 0, 650, 20), "PR (Peak Reference)", 0.95],
            [box(660, 0, 740, 20), "Z-score", 0.95],
            [box(750, 0, 900, 20), "AM (Age Matched)", 0.95],
            [box(0, 40, 70, 60), "Neck", 0.95],
            [box(80, 40, 160, 60), "5.81", 0.95],
            [box(170, 40, 250, 60), "4.96", 0.95],
            [box(260, 40, 360, 60), "0.854", 0.95],
            [box(380, 40, 460, 60), "0.0", 0.95],
            [box(470, 40, 650, 60), "101", 0.95],
            [box(660, 40, 740, 60), "1.0", 0.95],
            [box(750, 40, 900, 60), "117", 0.95],
            [box(0, 80, 70, 100), "Total", 0.95],
            [box(80, 80, 160, 100), "54.77", 0.95],
            [box(170, 80, 250, 100), "57.60", 0.95],
            [box(260, 80, 360, 100), "1.052", 0.95],
            [box(380, 80, 460, 100), "0.9", 0.95],
            [box(470, 80, 650, 100), "112", 0.95],
            [box(660, 80, 740, 100), "1.3", 0.95],
            [box(750, 80, 900, 100), "119", 0.95],
            [box(20, 160, 80, 180), "7.0", 0.95],
        ]

        data = p.parse_bmd_v2(ocr_res)

        self.assertEqual(data["t_score"], 0.0)
        self.assertEqual(data["z_score"], 1.0)
        self.assertTrue(data["has_neck"])

    def test_patient_info_accepts_dexa_overlay_age_and_sex(self):
        ocr_res = [
            [box(0, 0, 60, 20), "059Y", 0.95],
            [box(0, 25, 20, 45), "M", 0.95],
        ]

        info = p.parse_patient_info(ocr_res)

        self.assertEqual(info["Age"], 59)
        self.assertEqual(info["Sex"], "Male")

    def test_whole_body_parsing(self):
        ocr_res = [
            [box(0, 0, 100, 10), "Total Body % Fat", 0.95],
            [box(110, 0, 200, 10), "32.5", 0.95],
            [box(0, 40, 100, 50), "VAT Area", 0.95],
            [box(110, 40, 200, 50), "120 cm2", 0.95],
        ]

        data = p.parse_whole_body(ocr_res)

        self.assertEqual(data["fat_percent"], 32.5)
        self.assertEqual(data["vat_area"], 120.0)

    def test_ris_detects_calcium_mode(self):
        mode = p.detect_mode_from_ris(["Cardiac CT", "钙化指数分析(No Contrast)"])

        self.assertEqual(mode, "calcium")

    def test_calcium_score_parsing(self):
        ocr_res = [
            [box(0, 0, 80, 20), "Artery", 0.95],
            [box(100, 0, 180, 20), "Lesions", 0.95],
            [box(210, 0, 330, 20), "Volume / mm3", 0.95],
            [box(360, 0, 500, 20), "Equiv. Mass / mg", 0.95],
            [box(550, 0, 640, 20), "Score", 0.95],
            [box(0, 30, 80, 50), "LM", 0.95],
            [box(100, 30, 180, 50), "0", 0.95],
            [box(210, 30, 330, 50), "0.0", 0.95],
            [box(360, 30, 500, 50), "0.00", 0.95],
            [box(550, 30, 640, 50), "0.0", 0.95],
            [box(0, 60, 80, 80), "LAD", 0.95],
            [box(100, 60, 180, 80), "1", 0.95],
            [box(210, 60, 330, 80), "5.2", 0.95],
            [box(360, 60, 500, 80), "0.95", 0.95],
            [box(550, 60, 640, 80), "4.5", 0.95],
            [box(0, 90, 80, 110), "CX", 0.95],
            [box(550, 90, 640, 110), "0.0", 0.95],
            [box(0, 120, 80, 140), "RCA", 0.95],
            [box(550, 120, 640, 140), "0.0", 0.95],
            [box(0, 180, 80, 200), "Total", 0.95],
            [box(100, 180, 180, 200), "1", 0.95],
            [box(210, 180, 330, 200), "5.2", 0.95],
            [box(360, 180, 500, 200), "0.95", 0.95],
            [box(550, 180, 640, 200), "4.5", 0.95],
        ]

        data = p.parse_calcium_scores(ocr_res)

        self.assertTrue(data["is_valid"])
        self.assertEqual(data["LM"], 0.0)
        self.assertEqual(data["LAD"], 4.5)
        self.assertEqual(data["CX"], 0.0)
        self.assertEqual(data["RCA"], 0.0)
        self.assertEqual(data["Total"], 4.5)

    def test_calcium_score_parsing_merged_rows_and_lcx(self):
        ocr_res = [
            [box(0, 0, 640, 20), "Artery Lesions Volume Equiv Mass Score", 0.95],
            [box(0, 30, 640, 50), "L.MAIN 0 0.0 0.00 0.0", 0.95],
            [box(0, 60, 640, 80), "LAD 1 5.2 0.95 4.5", 0.95],
            [box(0, 90, 640, 110), "LCX 0 0.0 0.00 0.0", 0.95],
            [box(0, 120, 640, 140), "RCA 0 0.0 0.00 0.0", 0.95],
            [box(0, 180, 640, 200), "Total 1 5.2 0.95 4.5", 0.95],
        ]

        data = p.parse_calcium_scores(ocr_res)

        self.assertTrue(data["is_valid"])
        self.assertEqual(data["LM"], 0.0)
        self.assertEqual(data["LAD"], 4.5)
        self.assertEqual(data["CX"], 0.0)
        self.assertEqual(data["RCA"], 0.0)
        self.assertEqual(data["Total"], 4.5)

    def test_calcium_report_output(self):
        results_data = {"LM": 0.0, "LAD": 4.5, "CX": 0.0, "RCA": 0.0, "Total": 4.5}

        report, data = p.apply_clinical_logic({}, "calcium", results_data, {})

        self.assertIn("Agatston Score (Calcium Score)", report)
        self.assertIn("L.MAIN:  0", report)
        self.assertIn("LAD   :  4.5", report)
        self.assertIn("LCX   :  0", report)
        self.assertIn("RCA   :  0", report)
        self.assertIn("Total :  4.5", report)
        self.assertIn("Total Calcium Score was 4.5", report)
        self.assertIs(data, results_data)

    def test_calcium_report_uses_config_template(self):
        results_data = {"LM": 1.0, "LAD": 2.5, "CX": 3.0, "RCA": 4.0, "Total": 10.5}
        config = {"calcium_template": "Calcium\nLM={LM}\nLCX={LCX}\nTotal={Total}"}

        report, data = p.apply_clinical_logic({}, "calcium", results_data, config)

        self.assertEqual(report, "Calcium\r\nLM=1\r\nLCX=3\r\nTotal=10.5")
        self.assertIs(data, results_data)

    def test_clinical_logic_osteoporosis(self):
        patient_info = {"Sex": "Female", "Age": 65}
        results_data = {"t_score": -2.6, "z_score": -2.0, "has_neck": True}
        config = {}

        report, data = p.apply_clinical_logic(patient_info, "bmd", results_data, config)

        self.assertIn("osteoporosis", report.lower())
        self.assertEqual(data["classification"], "骨質疏鬆( osteoporosis )")


if __name__ == "__main__":
    unittest.main()
