import hashlib
import json

class TrendAnalyzer:
    def __init__(self, width, depth):
        self.width = width
        self.depth = depth
        self.sketch = [[0] * width for _ in range(depth)]
        self.hash_functions = self._create_hash_functions()

    def _create_hash_functions(self):
        hash_functions = []
        for i in range(self.depth):
            def _hash_func(x, salt=i):
                return int(hashlib.sha256(f"{x}{salt}".encode()).hexdigest(), 16)
            hash_functions.append(_hash_func)
        return hash_functions

    def add(self, item):
        for i in range(self.depth):
            index = self.hash_functions[i](item) % self.width
            self.sketch[i][index] += 1

    def estimate(self, item):
        min_count = float('inf')
        for i in range(self.depth):
            index = self.hash_functions[i](item) % self.width
            min_count = min(min_count, self.sketch[i][index])
        return min_count

if __name__ == '__main__':
    # Example usage with news data
    with open('news_data.json', 'r') as file:
        news_data = json.load(file)

    trend_analyzer = TrendAnalyzer(width=1000, depth=5)
    for article in news_data:
        trend_analyzer.add(article['category'])

    print("Category Frequency Estimates:")
    categories = set(article['category'] for article in news_data)
    for category in categories:
        estimate = trend_analyzer.estimate(category)
        print(f"Category: {category}, Estimated Frequency: {estimate}")
