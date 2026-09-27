import sys
import unittest
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from score import _ar_modellrelease_signal, final_score, prioritize_scoring_candidates  # noqa: E402


class ModelReleasePriorityTests(unittest.TestCase):
    def test_vendor_new_model_is_discovery_signal(self):
        candidate = {
            "title": "DeepSeek announces a new model with public API",
            "summary": "The model is now available to developers.",
        }
        self.assertTrue(_ar_modellrelease_signal(candidate))

    def test_generic_model_benchmark_is_not_release_signal(self):
        candidate = {
            "title": "Gemini benchmark results point to a strong next model",
            "summary": "Researchers compare performance across tasks.",
        }
        self.assertFalse(_ar_modellrelease_signal(candidate))

    def test_release_candidate_is_not_dropped_from_top_100(self):
        ordinary = [{"title": f"General AI update {i}", "summary": "news"} for i in range(100)]
        release = {"title": "Gemini 3.8 Flash released", "summary": "now available"}
        selected = prioritize_scoring_candidates(ordinary + [release], limit=100)
        self.assertIn(release, selected)
        self.assertEqual(len(selected), 100)

    def test_verified_release_beats_same_story_without_release_bonus(self):
        base = {
            "tier": 3,
            "source_weight": 20,
            "published": None,
            "_ai_score": {
                "score": 8,
                "lead_potential": 4,
                "actionable": True,
                "swedish_relevance": 1,
                "category": "Modeller",
            },
        }
        release = {**base, "_ai_score": {**base["_ai_score"], "model_release": True, "release_status": "released"}}
        rumor = {**base, "_ai_score": {**base["_ai_score"], "model_release": True, "release_status": "rumor"}}
        self.assertGreater(final_score(release), final_score(rumor))


if __name__ == "__main__":
    unittest.main()
