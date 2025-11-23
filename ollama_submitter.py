import requests
import json
import random
import ollama
import datetime
import uuid
import sys

def generate_news_article_llm():
    prompt = """
Generate a short JSON object representing a news article with the following fields:

- category: on of ["world", "technology", "sports", "entertainment","health", "business","politics"]
- headline: a realistic news headline
- content: a short paragraph summarizing the article

Return ONLY valid JSON. No backticks, no explanation.
"""

    response = ollama.generate(
        model="gemma3:1b",
        prompt=prompt
    )
    response = response['response']

    # Basic cleanup to ensure JSON validity
    while response and response[0] != '{': response = response[1:]
    while response and response[-1] != '}': response = response[:-1]
    
    # Parse LLM output
    print(f"LLM Response: {response}")
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        print("Failed to parse JSON from LLM response.")
        return(None)

    # Add ID and timestamps locally
    data["_id"] = str(uuid.uuid4())
    data["datePublished"] = datetime.datetime.now().isoformat()
    data["lastUpdated"] = datetime.datetime.now().isoformat()
    # Ensure category is set if LLM missed it or if we used fallback
    if "category" not in data or data["category"] not in ["world", "technology", "sports", "entertainment"]:
        data["category"] = random.choice(["world", "technology", "sports", "entertainment","health", "business","politics"])
        
    data["popularity_score"] = random.randint(1, 10)
    data["engagementLevel"] = random.choice(["low", "medium", "high"])

    return data

def submit_article(index, total):
    """
    Generate and submit a single news article to the API.
    """
    url = "https://hashingworkshoplogica-gjc2bhe2e8fpa3g3.brazilsouth-01.azurewebsites.net/api/submit/"
    
    print(f"[{index}/{total}] Generating article...")
    article = generate_news_article_llm()
    print(f"Generated: {article['headline']}")
    
    try:
        response = requests.post(url, json=article)
        if response.status_code in [200, 201]:
            print(f"✓ Successfully submitted article!")
        else:
            print(f"✗ Failed to submit article. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"✗ An error occurred: {e}")

if __name__ == '__main__':
    print("Ollama News Submitter")
    
    num_articles = 1
    if len(sys.argv) > 1:
        try:
            num_articles = int(sys.argv[1])
            if num_articles < 1:
                print("Number of articles must be at least 1. Using default 1.")
                num_articles = 1
        except ValueError:
            print(f"Invalid number '{sys.argv[1]}'. Using default 1.")
            num_articles = 1
            
    print(f"Will submit {num_articles} article(s).")
    
    for i in range(num_articles):
        submit_article(i + 1, num_articles)
        if i < num_articles - 1:
            print("-" * 40)
