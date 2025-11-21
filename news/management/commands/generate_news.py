from django.core.management.base import BaseCommand
import json
import random
from faker import Faker
import datetime

class Command(BaseCommand):
    help = 'Generates a specified number of news articles and saves them to a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('num_articles', type=int, help='The number of news articles to generate.')
        parser.add_argument('file_path', type=str, help='The path to the JSON file to save the news articles to.')

    def handle(self, *args, **options):
        num_articles = options['num_articles']
        file_path = options['file_path']
        fake = Faker()

        def generate_news_article():
            return {
                "_id": fake.uuid4(),
                "headline": fake.sentence(),
                "content": fake.paragraph(),
                "category": random.choice(["world", "technology", "sports", "entertainment"]),
                "datePublished": fake.date_time_this_decade().isoformat()
            }

        news_data = [generate_news_article() for _ in range(num_articles)]
        with open(file_path, 'w') as file:
            json.dump(news_data, file, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {num_articles} news articles and saved them to {file_path}'))
