"""
Markov Chain service for analyzing article category transitions.
Calculates transition probabilities and generates graph data.
"""
from collections import defaultdict
from .models import News


class MarkovChainService:
    """Service for calculating Markov chains based on article categories"""
    
    @staticmethod
    def calculate_transition_matrix():
        """
        Calculate the transition probability matrix for article categories.
        
        Returns:
            dict: Nested dictionary with transition probabilities
                  {from_category: {to_category: probability}}
        """
        # Get all articles ordered by publication date
        articles = News.objects.all().order_by('datePublished')
        
        if articles.count() < 2:
            return {}
        
        # Count transitions
        transitions = defaultdict(lambda: defaultdict(int))
        category_counts = defaultdict(int)
        
        # Iterate through consecutive pairs
        prev_article = None
        for article in articles:
            if prev_article is not None:
                from_cat = prev_article.category
                to_cat = article.category
                transitions[from_cat][to_cat] += 1
                category_counts[from_cat] += 1
            prev_article = article
        
        # Calculate probabilities
        transition_matrix = {}
        for from_cat, to_cats in transitions.items():
            transition_matrix[from_cat] = {}
            total = category_counts[from_cat]
            for to_cat, count in to_cats.items():
                transition_matrix[from_cat][to_cat] = round(count / total, 4)
        
        return transition_matrix
    
    @staticmethod
    def get_markov_graph_data():
        """
        Generate graph data for the Markov chain.
        Optimized for frontend visualization.
        
        Returns:
            dict: Graph data with nodes and edges
        """
        transition_matrix = MarkovChainService.calculate_transition_matrix()
        
        if not transition_matrix:
            return {
                "nodes": [],
                "edges": []
            }
        
        # Get all unique categories
        all_categories = set()
        for from_cat in transition_matrix.keys():
            all_categories.add(from_cat)
            for to_cat in transition_matrix[from_cat].keys():
                all_categories.add(to_cat)
        
        # Create nodes with article counts
        nodes = []
        for category in sorted(all_categories):
            article_count = News.objects.filter(category=category).count()
            nodes.append({
                "id": category,
                "label": category.capitalize(),
                "count": article_count
            })
        
        # Create edges with probabilities
        edges = []
        for from_cat, to_cats in transition_matrix.items():
            for to_cat, probability in to_cats.items():
                edges.append({
                    "from": from_cat,
                    "to": to_cat,
                    "probability": probability
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
