import unittest

from platform_routing import (
    MOD_ALT,
    MOD_SHIFT,
    build_hotkey_task_map,
    parse_hotkey,
    route_dexa_from_ris_lines,
)


class TestPlatformRouting(unittest.TestCase):
    def test_verified_standalone_hotkeys_route_into_one_unified_queue(self):
        config = {
            "hotkeys": {
                "start_scan": "alt+o",
                "toggle_bmd": "shift+2",
                "force_male": "shift+b",
                "force_female": "shift+g",
            }
        }

        task_map = build_hotkey_task_map(config)

        self.assertEqual(task_map[1], ("dexa_scan_ris", None))
        self.assertEqual(task_map[2], ("dexa_toggle", None))
        self.assertEqual(task_map[3], ("bone_age", "M"))
        self.assertEqual(task_map[4], ("bone_age", "F"))

    def test_ris_lines_dispatch_dexa_mode_to_configured_monitor(self):
        config = {
            "monitors": {
                "dexa_wb": 1,
                "dexa_bmd": 2,
                "dexa_calcium": 3,
            }
        }

        self.assertEqual(
            route_dexa_from_ris_lines(["DEXA", "Whole Body"], config),
            ("dexa", {"mode": "whole_body", "monitor_idx": 1, "is_manual": False}),
        )
        self.assertEqual(
            route_dexa_from_ris_lines(["DEXA", "BMD"], config),
            ("dexa", {"mode": "bmd", "monitor_idx": 2, "is_manual": False}),
        )
        self.assertEqual(
            route_dexa_from_ris_lines(["Cardiac CT", "calcium score"], config),
            ("dexa", {"mode": "calcium", "monitor_idx": 3, "is_manual": False}),
        )

    def test_whole_body_ris_text_wins_over_generic_bone_density_noise(self):
        config = {
            "monitors": {
                "dexa_wb": 1,
                "dexa_bmd": 2,
                "dexa_calcium": 3,
            }
        }
        ris_lines = [
            "文字報告－骨密體脂肪分析Whole Body(自)",
            "Body Composition Assessment",
            "骨質密度自費查",
            "1.Total body fat percentage: 37.8%",
            "Female:normal:<25%;overweight:25%~38%;obesity:>=38%",
        ]

        self.assertEqual(
            route_dexa_from_ris_lines(ris_lines, config),
            ("dexa", {"mode": "whole_body", "monitor_idx": 1, "is_manual": False}),
        )

    def test_bmd_title_wins_over_historical_whole_body_noise(self):
        config = {
            "monitors": {
                "dexa_wb": 1,
                "dexa_bmd": 2,
                "dexa_calcium": 3,
            }
        }
        ris_lines = [
            "文字報告－骨質密度自費查",
            "Body Composition Assessment",
            "1.Total body fat percentage: 37.8%",
        ]

        self.assertEqual(
            route_dexa_from_ris_lines(ris_lines, config),
            ("dexa", {"mode": "bmd", "monitor_idx": 2, "is_manual": False}),
        )

    def test_title_ocr_missing_report_character_still_routes_whole_body(self):
        config = {"monitors": {"dexa_wb": 1, "dexa_bmd": 2, "dexa_calcium": 3}}

        self.assertEqual(
            route_dexa_from_ris_lines(["文字告－骨密體脂肪分析Whble Bd(自費)"], config),
            ("dexa", {"mode": "whole_body", "monitor_idx": 1, "is_manual": False}),
        )

    def test_verified_hotkey_strings_parse_to_windows_modifiers_and_vk(self):
        self.assertEqual(parse_hotkey("alt+o"), (MOD_ALT, ord("O")))
        self.assertEqual(parse_hotkey("shift+2"), (MOD_SHIFT, ord("2")))
        self.assertEqual(parse_hotkey("shift+b"), (MOD_SHIFT, ord("B")))
        self.assertEqual(parse_hotkey("shift+g"), (MOD_SHIFT, ord("G")))
        self.assertEqual(parse_hotkey("scroll_lock"), (0, 0x91))

    def test_invalid_hotkey_string_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_hotkey("shift+")


if __name__ == "__main__":
    unittest.main()
