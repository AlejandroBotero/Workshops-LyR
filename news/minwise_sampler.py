import hashlib
import heapq # For efficiently maintaining a min-heap (top-k smallest hashes)

class MinWiseSampler:
    def __init__(self, sample_size: int):
        """
        Initializes a MinWise Sampler.
        Maintains a fixed-size sample of articles for each category based on their hash.

        :param sample_size: The desired number of articles to keep in the sample for each category.
        """
        if not sample_size > 0:
            raise ValueError("Sample size must be greater than 0.")
        self.sample_size = sample_size
        # Stores a dictionary where keys are categories and values are min-heaps
        # Each item in the heap is (hash_value, article)
        self.category_samples = {}
        # Used to hash the article content
        self.hasher = hashlib.sha256

    def _hash_article(self, article: dict) -> int:
        """
        Generates a hash for the article's identifying content.
        """
        headline = article.get('headline', '')
        content = article.get('content', '')
        combined_text = f"{headline}-{content}"
        return int(self.hasher(combined_text.encode('utf-8')).hexdigest(), 16)

    def add_article(self, article: dict, category: str):
        """
        Adds an article to the sample for its given category.
        If the sample size is exceeded, only the article with the smallest hash value is kept.
        """
        article_hash = self._hash_article(article)

        if category not in self.category_samples:
            self.category_samples[category] = [] # Initialize as an empty list (will be a min-heap)

        current_sample = self.category_samples[category]

        if len(current_sample) < self.sample_size:
            heapq.heappush(current_sample, (article_hash, article))
        else:
            # If the current article's hash is smaller than the largest hash in the sample,
            # replace the largest with the current article.
            # In a min-heap, the largest element is effectively at the "bottom" after pushing,
            # but we want to check against the current largest *before* adding and pushing.
            # A more common approach for fixed-size reservoir sampling with min-hash
            # is to keep the k smallest hashes.
            # So, if current_article_hash < largest_hash_in_sample, replace.
            # Using a min-heap of size k, we push new item, then pop largest.
            # In Python's heapq, it's a min-heap. So we need to push and pop.
            heapq.heappushpop(current_sample, (article_hash, article))

    def get_sample(self, category: str) -> list[dict]:
        """
        Returns the representative sample of articles for a given category.
        """
        if category in self.category_samples:
            # Return only the article dictionaries, sorted by their hash (smallest first)
            return [article for hash_val, article in sorted(self.category_samples[category])]
        return []

    def get_all_samples(self) -> dict[str, list[dict]]:
        """
        Returns all representative samples, categorized.
        """
        all_samples = {}
        for category, sample_heap in self.category_samples.items():
            all_samples[category] = [article for hash_val, article in sorted(sample_heap)]
        return all_samples

    def clear(self):
        """
        Clears all samples.
        """
        self.category_samples = {}
