import math
import hashlib

class BloomFilter:
    def __init__(self, capacity: int, error_rate: float):
        """
        Initializes a Bloom Filter.

        :param capacity: Expected number of items to be added.
        :param error_rate: Desired false positive probability (e.g., 0.01 for 1%).
        """
        if not (0 < error_rate < 1):
            raise ValueError("Error rate must be between 0 and 1.")
        if not capacity > 0:
            raise ValueError("Capacity must be greater than 0.")

        self.capacity = capacity
        self.error_rate = error_rate
        self.num_bits = self._get_num_bits(capacity, error_rate)
        self.num_hashes = self._get_num_hashes(self.num_bits, capacity)
        self.bit_array = bytearray(math.ceil(self.num_bits / 8)) # Use bytearray for memory efficiency
        self.count = 0 # Number of items added

    def _get_num_bits(self, capacity: int, error_rate: float) -> int:
        """
        Calculates the optimal number of bits for the Bloom Filter.
        m = -(n * ln(p)) / (ln(2)^2)
        """
        return math.ceil(-(capacity * math.log(error_rate)) / (math.log(2) ** 2))

    def _get_num_hashes(self, num_bits: int, capacity: int) -> int:
        """
        Calculates the optimal number of hash functions.
        k = (m / n) * ln(2)
        """
        return math.ceil((num_bits / capacity) * math.log(2))

    def _hash(self, item: str, seed: int) -> int:
        """
        Generates a hash for the item using SHA256 and a seed.
        """
        s = hashlib.sha256(f"{item}-{seed}".encode('utf-8')).hexdigest()
        return int(s, 16)

    def add(self, item: str):
        """
        Adds an item to the Bloom Filter.
        """
        if self.count >= self.capacity:
            # Optionally, you could resize the filter or warn the user.
            # For simplicity, we'll just stop adding for now.
            # A Bloom Filter's error rate increases significantly past its capacity.
            print(f"Warning: Bloom Filter capacity ({self.capacity}) exceeded. Error rate will increase.")
            return

        for i in range(self.num_hashes):
            index = self._hash(item, i) % self.num_bits
            byte_index = index // 8
            bit_offset = index % 8
            self.bit_array[byte_index] |= (1 << bit_offset)
        self.count += 1

    def __contains__(self, item: str) -> bool:
        """
        Checks if an item might be in the Bloom Filter (with a certain false positive probability).
        """
        for i in range(self.num_hashes):
            index = self._hash(item, i) % self.num_bits
            byte_index = index // 8
            bit_offset = index % 8
            if not (self.bit_array[byte_index] & (1 << bit_offset)):
                return False # Definitely not in the set
        return True # Potentially in the set (might be a false positive)

    def clear(self):
        """
        Resets the Bloom Filter.
        """
        self.bit_array = bytearray(math.ceil(self.num_bits / 8))
        self.count = 0
