import hashlib
import random
import math

class AMSMomentEstimator:
    def __init__(self, num_estimators: int, max_value_range: int = 2**32 - 1):
        """
        Initializes the Alon-Matias-Szegedy (AMS) second frequency moment estimator.

        :param num_estimators: Number of independent estimators for averaging to reduce variance.
        :param max_value_range: The maximum possible value for the hash output.
                                 Used to define the range of the random variable.
        """
        if not num_estimators > 0:
            raise ValueError("Number of estimators must be greater than 0.")
        self.num_estimators = num_estimators
        self.max_value_range = max_value_range # Represents the size of the universe for hashing

        self.X = [] # List of (hash_seed, value, count) for each estimator
        for _ in range(num_estimators):
            # Each estimator needs a random hash function (represented by a seed)
            # and maintains a count for the items seen with that hash value.
            # We also need a random permutation/value for each item.
            # For the second moment, we need a random variable X_i for each distinct item.
            # X_i = 1 or -1 with probability 0.5.
            # When an item appears, we add X_i to a sum for that specific estimator.
            self.X.append({
                'seed': random.randint(0, self.max_value_range),
                'sum_of_random_variables': 0, # Sum of X_i for items mapped to this estimator
                'random_variables': {} # Stores (item -> X_i) for items mapped to this estimator
            })

    def _hash_item_to_estimator(self, item: str, seed: int) -> int:
        """
        Hashes an item to one of the estimators (0 to num_estimators-1).
        """
        s = hashlib.sha256(f"{item}-{seed}".encode('utf-8')).hexdigest()
        return int(s, 16) % self.num_estimators

    def _get_random_variable(self, item: str, estimator_seed: int) -> int:
        """
        Generates a random variable (1 or -1) for a given item,
        consistent for that item within an estimator.
        """
        rv_seed = f"{item}-{estimator_seed}-rv".encode('utf-8')
        hash_val = int(hashlib.sha256(rv_seed).hexdigest(), 16)
        return 1 if hash_val % 2 == 0 else -1

    def add(self, item: str):
        """
        Adds an item to the estimator.
        """
        # For simplicity in this demo, we'll assume the item is the article identifier
        # and we are interested in its 'category' as the "element" whose frequency we track.
        # This implementation tracks the second moment of arbitrary string 'items'.
        
        # We need a random variable for each distinct item (category hash)
        # This implementation assumes the 'item' itself is what we are counting frequencies for.
        # So if 'item' is a category, we are tracking frequencies of categories.
        # The AMS algorithm is more complex if we want to weight by engagement *per item*.
        # Let's simplify: we're counting second moment of categories.
        # If 'item' is the category, we're adding its count.

        # The description "Analyze the variability in article sharing and engagement metrics"
        # suggests the values we are adding are the engagement levels, not just categories.
        # Let's assume 'item' passed to add is actually the numerical engagement level (1, 2, 3)
        # and we want to estimate SUM(f_i^2) where f_i is frequency of each engagement level.
        # This is a bit of a misinterpretation of "higher order moments" for *categories*.
        # If it's about categories, we need to map categories to distinct elements.

        # Re-evaluating: "variability in article sharing and engagement metrics."
        # This means for a *given article*, what is its "engagement metric" value.
        # We want sum(engagement_level_i^2) over all articles. That's the 2nd moment of engagement levels.
        # OR we want sum( (count of articles with engagement_level X)^2 ) over all X.
        # The former (sum of engagement_level_i^2) is simpler and makes more sense with the prompt.
        #
        # Let 'item' be the string representation of the article (headline+content)
        # Let 'value' be its numerical engagement level (1, 2, or 3)
        # We want to estimate sum_{articles i} (engagement_level_i)^2
        # This requires a different type of AMS estimator or a different application.

        # The simpler interpretation of AMS is to estimate sum(f_i^2) where f_i is the frequency
        # of distinct items. If the items are categories, then it's sum( (count of category X)^2 ).
        # If the items are engagement levels, it's sum( (count of engagement level X)^2 ).

        # Let's assume the user wants the second moment of the *category frequencies*.
        # i.e. sum of (count of category C)^2.
        # So, 'item' will be the category string (e.g., "world", "technology").
        # The `add` method should just add the category.

        # Let's stick to the interpretation that 'item' is the category.
        # The AMS algorithm typically samples random hash functions for each stream element.
        # The specific implementation for sum of squares (F2) uses a single hash value
        # h(x) -> 1 or -1, and for each element x, adds h(x) to a counter for a random bucket.

        # The provided AMS skeleton is more complex than a standard single-pass F2 estimator.
        # A simple F2 estimator for SUM(f_i^2) works like this:
        # Choose a random hash function h: U -> {1, -1}
        # Maintain a counter Z. For each item i in stream, Z = Z + h(i).
        # E[Z^2] = F2. So Z^2 is an unbiased estimator. Multiple estimators reduce variance.

        # Let's simplify the AMS structure to a standard F2 estimator.
        # We will estimate sum(freq_i^2) where freq_i is the frequency of each category.

        # num_estimators: Number of independent random variables to average.
        # Each estimator will have its own random variables X_i for each distinct item.
        # When an item 'j' arrives, we update Z_k = Z_k + X_{k,j} (where X_{k,j} is +/-1 for item j in estimator k)
        # Then the estimate is average(Z_k^2).

        # Let 'item' be the distinct item (e.g., "world", "technology", etc.)

        for k in range(self.num_estimators):
            # For each item, generate a random variable (1 or -1) consistent for that item
            # within this estimator (k).
            if item not in self.X[k]['random_variables']:
                self.X[k]['random_variables'][item] = self._get_random_variable(item, self.X[k]['seed'])
            
            self.X[k]['sum_of_random_variables'] += self.X[k]['random_variables'][item]

    def estimate_second_moment(self) -> int:
        """
        Estimates the second frequency moment (F2 = sum(f_i^2)).
        """
        if not self.X:
            return 0

        estimates = []
        for k in range(self.num_estimators):
            estimates.append(self.X[k]['sum_of_random_variables'] ** 2)
        
        # Average the estimates to reduce variance
        if estimates:
            return int(sum(estimates) / len(estimates))
        return 0

    def clear(self):
        """
        Resets the estimator.
        """
        self.X = []
        for _ in range(self.num_estimators):
            self.X.append({
                'seed': random.randint(0, self.max_value_range),
                'sum_of_random_variables': 0,
                'random_variables': {}
            })
