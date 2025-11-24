import requests
import json
import random
import time
from faker import Faker
import datetime

fake = Faker()

def generate_news_article():
    return {
        "headline": fake.sentence(),
        "content": fake.paragraph(),
        "category": random.choice(["world", "technology", "sports", "entertainment"]),
        "datePublished": fake.date_time_this_decade().isoformat(),
        "popularity_score": random.randint(1, 10), # Simulate popularity
        "engagementLevel": random.choice(["low", "medium", "high"]),
        "lastUpdated": datetime.datetime.now().isoformat(),
    }

def submit_news(n=1):
    url = "http://127.0.0.1:8000/news/submit/"
    for _ in range(n):
        article = generate_news_article()
        try:
            print("before posting")
            response = requests.post(url, json=article)
            print("after posting")
            if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                print(f"Successfully submitted article: {article['headline']}")
            else:
                print(f"Failed to submit article. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        
        sleep_time = random.uniform(1, 3)
        print(f"Waiting for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)

if __name__ == '__main__':
    print("started process")
    submit_news()

