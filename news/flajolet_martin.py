import hashlib
import math
import random

class FlajoletMartin:
    def __init__(self, num_bits: int = 64, num_hash_functions: int = 1):
        """
        Initializes the Flajolet-Martin algorithm estimator.

        :param num_bits: The number of bits for the hash function output (e.g., 32 or 64).
        :param num_hash_functions: The number of independent hash functions to use for averaging.
                                   For simplicity, we'll start with 1, but for better accuracy, >1 is recommended.
        """
        if not num_bits > 0:
            raise ValueError("num_bits must be greater than 0.")
        if not num_hash_functions > 0:
            raise ValueError("num_hash_functions must be greater than 0.")

        self.num_bits = num_bits
        self.num_hash_functions = num_hash_functions
        self.R = [0] * num_hash_functions  # Max trailing zeros for each hash function
        self.hash_seeds = [random.randint(0, 2**32 - 1) for _ in range(num_hash_functions)]
        self.alpha = 0.77351 # Empirical constant for bias correction

    def _hash_item(self, item: str, seed: int) -> int:
        """
        Generates a hash for the item, using SHA256 and a seed,
        and ensures it fits within num_bits.
        """
        combined = f"{item}-{seed}".encode('utf-8')
        s = hashlib.sha256(combined).hexdigest()
        # Convert hex digest to integer and truncate to num_bits
        return int(s, 16) % (2 ** self.num_bits)

    def _rho(self, value: int) -> int:
        """
        Calculates the position of the least significant bit (LSB) that is 1.
        e.g., rho(12) (binary 1100) = 2 (0-indexed)
        """
        if value == 0:
            return self.num_bits # Or raise error, or define as max bits + 1
        return (value & -value).bit_length() - 1 # Python's way to get LSB position

    def add(self, item: str):
        """
        Adds an item to the estimator.
        """
        for i in range(self.num_hash_functions):
            hashed_value = self._hash_item(item, self.hash_seeds[i])
            self.R[i] = max(self.R[i], self._rho(hashed_value))

    def estimate_distinct_count(self) -> int:
        """
        Estimates the number of distinct elements.
        """
        if not self.R:
            return 0 # No items added yet

        # Average the rho values and apply the constant
        avg_R = sum(self.R) / self.num_hash_functions
        estimate = (2 ** avg_R) / self.alpha
        return int(estimate)

    def clear(self):
        """
        Resets the estimator.
        """
        self.R = [0] * self.num_hash_functions
        self.hash_seeds = [random.randint(0, 2**32 - 1) for _ in range(self.num_hash_functions)]
