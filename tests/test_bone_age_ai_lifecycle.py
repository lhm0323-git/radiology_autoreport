import unittest
from types import ModuleType
from unittest.mock import patch

import main


class FakeBoneAgeAIEngine:
    instances = 0

    def __init__(self):
        FakeBoneAgeAIEngine.instances += 1

    def predict(self, image, is_female):
        return 42.0


class TestBoneAgeAiLifecycle(unittest.TestCase):
    def test_lazy_bone_age_ai_unload_releases_engine_and_reload_on_next_predict(self):
        FakeBoneAgeAIEngine.instances = 0
        lazy_ai = main.LazyBoneAgeAI()
        fake_module = ModuleType("ai_engine")
        fake_module.BoneAgeAIEngine = FakeBoneAgeAIEngine

        with patch.dict("sys.modules", {"ai_engine": fake_module}):
            self.assertEqual(lazy_ai.predict(None, False), 42.0)
            self.assertEqual(FakeBoneAgeAIEngine.instances, 1)

            self.assertTrue(lazy_ai.unload())
            self.assertFalse(lazy_ai.unload())

            self.assertEqual(lazy_ai.predict(None, True), 42.0)
            self.assertEqual(FakeBoneAgeAIEngine.instances, 2)


if __name__ == "__main__":
    unittest.main()
