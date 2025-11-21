import hashlib
import re

# SimHash constants
SIMHASH_BITS = 64 # Using 64-bit simhash

def _get_feature_vector(text):
    """
    Generates a feature vector for SimHash from the given text (headline).
    Simple tokenization and hashing of each token.
    """
    # Simple tokenization: split by non-alphanumeric characters and convert to lowercase
    words = re.findall(r'\b\w+\b', text.lower())
    
    features = []
    for word in words:
        # Use SHA1 for hashing individual tokens (can be any good hash function)
        hash_val = int(hashlib.sha1(word.encode('utf-8')).hexdigest(), 16)
        features.append(hash_val)
    return features

def simhash_news_object(news_object):
    """
    Generates a SimHash for a news object based ONLY on its headline.
    """
    headline = news_object.get('headline', '')
    
    if not headline:
        return 0 # Return a default simhash for empty headlines

    features = _get_feature_vector(headline)
    
    v = [0] * SIMHASH_BITS
    for feature_hash in features:
        for i in range(SIMHASH_BITS):
            if (feature_hash >> i) & 1:
                v[i] += 1
            else:
                v[i] -= 1
    
    simhash_value = 0
    for i in range(SIMHASH_BITS):
        if v[i] >= 0:
            simhash_value |= (1 << i)
    return simhash_value

def get_hamming_distance(hash1, hash2):
    """
    Calculates the Hamming distance between two SimHashes.
    """
    x = hash1 ^ hash2
    count = 0
    while x > 0:
        x &= (x - 1) # Brian Kernighan's algorithm to count set bits
        count += 1
    return count

def get_sha256_hash(news_object):
    """
    Generates a SHA256 hash for a news object based on its headline and content.
    (Kept for reference/original functionality if needed)
    """
    headline = news_object.get('headline', '')
    content = news_object.get('content', '')
    
    combined_string = f"{headline}{content}".encode('utf-8')
    
    hasher = hashlib.sha256()
    hasher.update(combined_string)
    return hasher.hexdigest()

# The original compare_news_objects will now be based on SimHash
def compare_news_objects(news_object1, news_object2):
    """
    Compares two news objects using SimHash on their headlines and returns the Hamming distance.
    Lower Hamming distance means higher similarity.
    """
    simhash1 = simhash_news_object(news_object1)
    simhash2 = simhash_news_object(news_object2)
    return get_hamming_distance(simhash1, simhash2)