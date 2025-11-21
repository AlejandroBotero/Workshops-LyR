import unittest
import json
import os
from src.hashing.categorizer import ArticleCategorizer

class TestArticleCategorizer(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {"category": "tech", "title": "t1"},
            {"category": "sports", "title": "s1"},
            {"category": "tech", "title": "t2"},
        ]
        self.test_file = 'test_news_data.json'
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f)
        self.categorizer = ArticleCategorizer(self.test_file)

    def tearDown(self):
        os.remove(self.test_file)

    def test_categorize_articles(self):
        categorized = self.categorizer.categorize_articles()
        self.assertIn('tech', categorized)
        self.assertIn('sports', categorized)
        self.assertEqual(len(categorized['tech']), 2)
        self.assertEqual(len(categorized['sports']), 1)

if __name__ == '__main__':
    unittest.main()
