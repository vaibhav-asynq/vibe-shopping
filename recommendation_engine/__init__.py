"""
Recommendation Engine for Vibe Shopping

Progressive confidence-based product matching system.
"""

from .models import Product, AttributeFilter, PriceFilter
from .catalog import ProductCatalog
from .progressive_matcher import ProgressiveMatcher
from .llm_ranker import LLMRanker
from .enhanced_matcher import EnhancedProgressiveMatcher, HybridMatcher

__all__ = [
    'Product', 'AttributeFilter', 'PriceFilter', 
    'ProductCatalog', 'ProgressiveMatcher',
    'LLMRanker', 'EnhancedProgressiveMatcher', 'HybridMatcher'
]
