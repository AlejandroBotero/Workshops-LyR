import unittest
from .hasher import hash_news_object, compare_news_objects

class TestHasher(unittest.TestCase):

    def test_hash_news_object_consistent(self):
        news1 = {'headline': 'Test Headline', 'content': 'Test Content'}
        news2 = {'headline': 'Test Headline', 'content': 'Test Content'}
        self.assertEqual(hash_news_object(news1), hash_news_object(news2))

    def test_hash_news_object_different(self):
        news1 = {'headline': 'Test Headline', 'content': 'Test Content'}
        news2 = {'headline': 'Another Headline', 'content': 'Test Content'}
        self.assertNotEqual(hash_news_object(news1), hash_news_object(news2))

    def test_hash_news_object_empty_fields(self):
        news1 = {'headline': '', 'content': 'Test Content'}
        news2 = {'headline': '', 'content': 'Test Content'}
        self.assertEqual(hash_news_object(news1), hash_news_object(news2))

        news3 = {'headline': 'Test Headline', 'content': ''}
        news4 = {'headline': 'Test Headline', 'content': ''}
        self.assertEqual(hash_news_object(news3), hash_news_object(news4))

        news5 = {'headline': '', 'content': ''}
        news6 = {'headline': '', 'content': ''}
        self.assertEqual(hash_news_object(news5), hash_news_object(news6))

    def test_compare_news_objects_identical(self):
        news1 = {'headline': 'Test Headline', 'content': 'Test Content'}
        news2 = {'headline': 'Test Headline', 'content': 'Test Content'}
        self.assertTrue(compare_news_objects(news1, news2))

    def test_compare_news_objects_different(self):
        news1 = {'headline': 'Test Headline', 'content': 'Test Content'}
        news2 = {'headline': 'Another Headline', 'content': 'Test Content'}
        self.assertFalse(compare_news_objects(news1, news2))

    def test_compare_news_objects_missing_keys(self):
        news1 = {'headline': 'Test Headline'}
        news2 = {'headline': 'Test Headline', 'content': ''}
        self.assertTrue(compare_news_objects(news1, news2)) # Both should hash as 'Test Headline' + ''

        news3 = {'content': 'Test Content'}
        news4 = {'headline': '', 'content': 'Test Content'}
        self.assertTrue(compare_news_objects(news3, news4)) # Both should hash as '' + 'Test Content'

        news5 = {}
        news6 = {'headline': '', 'content': ''}
        self.assertTrue(compare_news_objects(news5, news6)) # Both should hash as '' + ''

if __name__ == '__main__':
    unittest.main()