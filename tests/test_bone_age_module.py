import unittest

from modules.bone_age import format_bone_age, resolve_gender_from_ocr_texts


class TestBoneAgeFormatting(unittest.TestCase):
    def test_month_range_floors_at_eight_months(self):
        result = format_bone_age(5.0, is_female=False, offset_months=0.0)

        self.assertEqual(result["bookmark_target"], "8-month-old boy")

    def test_half_year_range_for_two_to_six_years(self):
        result = format_bone_age(30.0, is_female=True, offset_months=0.0)

        self.assertEqual(result["report_age"], "2.5-3 years")
        self.assertEqual(result["bookmark_target"], "2.5-year-old girl")

    def test_integer_year_range_for_six_and_above(self):
        result = format_bone_age(135.7, is_female=True, offset_months=0.0)

        self.assertEqual(result["report_age"], "11-12 year")
        self.assertEqual(result["bookmark_target"], "11-year-old girl")

    def test_applies_calibration_offset_before_bookmark_target(self):
        result = format_bone_age(27.05, is_female=False, offset_months=-5.0)

        self.assertEqual(result["calibrated_months"], 22.05)
        self.assertEqual(result["report_age"], "22-24 months")
        self.assertEqual(result["bookmark_target"], "2-year-old boy")

    def test_gender_ocr_missing_is_unknown_not_default_male_or_female(self):
        result = resolve_gender_from_ocr_texts(["R11394", "2022/10/28", "003Y", "IM:1"])

        self.assertIsNone(result)

    def test_gender_ocr_accepts_explicit_tokens(self):
        self.assertFalse(resolve_gender_from_ocr_texts(["003Y", "M"]))
        self.assertTrue(resolve_gender_from_ocr_texts(["Sex:F"]))


if __name__ == "__main__":
    unittest.main()
