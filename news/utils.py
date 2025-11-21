import json
import hashlib

class ArticleCategorizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.categories = {}

    def load_data(self):
        with open(self.data_path, 'r') as file:
            return json.load(file)

    def categorize_articles(self):
        articles = self.load_data()
        for article in articles:
            category = article.get('category')
            if category:
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(article)
        return self.categories

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
