import json

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

if __name__ == '__main__':
    categorizer = ArticleCategorizer('news_data.json')
    categorized_articles = categorizer.categorize_articles()
    for category, articles in categorized_articles.items():
        print(f"Category: {category}, Articles: {len(articles)}")
