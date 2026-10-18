import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import score
import validate
import write


class EditorialBalanceTests(unittest.TestCase):
    def test_major_policy_news_beats_minor_release(self):
        def candidate(category, news, lead, actionable, release=False):
            return {'_ai_score': {'category': category, 'score': news,
                    'lead_potential': lead, 'actionable': actionable,
                    'model_release': release, 'release_status': 'released'}}
        self.assertGreater(
            score.final_score(candidate('Politik', 9, 5, False)),
            score.final_score(candidate('Modeller', 6, 3, True, True)))

    def test_safety_candidate_survives_release_heavy_scoring_batch(self):
        releases = [{'title': f'Gemini model released {i}'} for i in range(100)]
        safety = {'title': 'Frontier AI safety evaluation finds unauthorized actions'}
        selected = score.prioritize_scoring_candidates(releases + [safety], 100)
        self.assertIn(safety, selected)
        self.assertEqual(len(selected), 100)

    def test_policy_lead_passes_segment_validation(self):
        issue = {'frontmatter': {'lead': {'segment': 'bransch',
                 'kicker': 'Politik', 'headline': 'EU AI regulation'}}}
        self.assertTrue(validate._check_lead_verktyg(issue, [])['ok'])

    def test_unknown_lead_segment_is_rejected(self):
        issue = {'frontmatter': {'lead': {'segment': 'invented'}}}
        self.assertFalse(validate._check_lead_verktyg(issue, [])['ok'])


if __name__ == '__main__':
    unittest.main()
