import unittest
from src.trends.analyzer import TrendAnalyzer

class TestTrendAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TrendAnalyzer(width=100, depth=5)

    def test_add_and_estimate(self):
        self.analyzer.add("apple")
        self.analyzer.add("apple")
        self.analyzer.add("banana")
        
        apple_estimate = self.analyzer.estimate("apple")
        banana_estimate = self.analyzer.estimate("banana")
        orange_estimate = self.analyzer.estimate("orange")

        self.assertGreaterEqual(apple_estimate, 2)
        self.assertGreaterEqual(banana_estimate, 1)
        self.assertGreaterEqual(orange_estimate, 0)

if __name__ == '__main__':
    unittest.main()
