import unittest

from workstation_log_check import check_workstation_log


class TestWorkstationLogCheck(unittest.TestCase):
    def test_accepts_same_session_dexa_bone_age_dexa_with_toggle(self):
        text = """
        [09:00:00] Radiology Auto-Reporter running.
        [09:00:01] Processing Task: dexa (Param: {'mode': 'bmd'})
        [09:00:02] DEXA Done!
        [09:00:03] Processing Task: bone_age (Param: F)
        [09:00:04] PDF Viewer open (HWND: 123). Jumping to page 76
        [09:00:05] Bone Age Done!
        [09:00:05] Processing Task: dexa_toggle (Param: None)
        [09:00:06] DEXA Done!
        [09:00:07] Processing Task: dexa (Param: {'mode': 'calcium'})
        [09:00:08] DEXA Done!
        """

        result = check_workstation_log(text)

        self.assertTrue(result.ok, result)
        self.assertEqual(result.missing, [])
        self.assertEqual(result.failures, [])

    def test_rejects_missing_return_to_dexa(self):
        text = """
        [09:00:01] Processing Task: dexa (Param: {'mode': 'bmd'})
        [09:00:02] DEXA Done!
        [09:00:03] Processing Task: bone_age (Param: F)
        [09:00:04] PDF Viewer open (HWND: 123). Jumping to page 76
        [09:00:04] Bone Age Done!
        [09:00:05] Processing Task: dexa_toggle (Param: None)
        [09:00:06] DEXA Done!
        """

        result = check_workstation_log(text)

        self.assertFalse(result.ok)
        self.assertIn("dexa -> bone_age -> dexa sequence", result.missing)

    def test_rejects_error_patterns(self):
        text = """
        [09:00:01] Processing Task: dexa (Param: {'mode': 'bmd'})
        [09:00:02] DEXA Done!
        [09:00:03] Processing Task: bone_age (Param: F)
        [09:00:04] PDF Viewer open (HWND: 123). Jumping to page 76
        [09:00:04] Bone Age Done!
        [09:00:05] Processing Task: dexa (Param: {'mode': 'calcium'})
        [09:00:06] DEXA Done!
        [09:00:06] Processing Task: dexa_toggle (Param: None)
        [09:00:06] DEXA Done!
        [09:00:07] Error processing: Clipboard failed
        """

        result = check_workstation_log(text)

        self.assertFalse(result.ok)
        self.assertIn("Error processing:", result.failures)

    def test_rejects_missing_pdf_navigation_evidence(self):
        text = """
        [09:00:01] Processing Task: dexa (Param: {'mode': 'bmd'})
        [09:00:02] DEXA Done!
        [09:00:03] Processing Task: bone_age (Param: F)
        [09:00:04] Bone Age Done!
        [09:00:05] Processing Task: dexa_toggle (Param: None)
        [09:00:06] DEXA Done!
        [09:00:07] Processing Task: dexa (Param: {'mode': 'calcium'})
        [09:00:08] DEXA Done!
        """

        result = check_workstation_log(text)

        self.assertFalse(result.ok)
        self.assertIn("Bone Age PDF navigation evidence", result.missing)


if __name__ == "__main__":
    unittest.main()
