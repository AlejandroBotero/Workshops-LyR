from src.hashing.categorizer import ArticleCategorizer
from src.trends.analyzer import TrendAnalyzer

class CLIDashboard:
    def __init__(self, data_path):
        self.data_path = data_path
        self.categorizer = ArticleCategorizer(data_path)
        self.trend_analyzer = TrendAnalyzer(width=1000, depth=5)

    def run(self):
        print("Processing news data...")
        categorized_articles = self.categorizer.categorize_articles()
        
        print("\n--- Article Categorization ---")
        for category, articles in categorized_articles.items():
            print(f"Category: {category}, Articles: {len(articles)}")

        print("\n--- Trend Analysis ---")
        articles = self.categorizer.load_data()
        for article in articles:
            self.trend_analyzer.add(article['category'])

        categories = set(article['category'] for article in articles)
        for category in categories:
            estimate = self.trend_analyzer.estimate(category)
            print(f"Category: {category}, Estimated Frequency: {estimate}")

if __name__ == '__main__':
    dashboard = CLIDashboard('news_data.json')
    dashboard.run()
