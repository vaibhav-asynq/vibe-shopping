"""
Enhanced two-stage recommendation system:
Stage 1: Progressive filtering to get 15 candidates
Stage 2: LLM ranking to select top 5
"""
from typing import List, Dict, Any, Union
from .models import Product, AttributeFilter, PriceFilter
from .catalog import ProductCatalog
from .progressive_matcher import ProgressiveMatcher
from .llm_ranker import LLMRanker


class EnhancedProgressiveMatcher:
    """Two-stage recommendation system with LLM-powered intelligent ranking"""
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
        self.candidate_count = 15  # Stage 1: Get 15 diverse candidates
        self.final_count = 5       # Stage 2: LLM picks top 5
        
        # Initialize components
        self.progressive_matcher = ProgressiveMatcher(catalog)
        self.llm_ranker = LLMRanker()
        
        # Override progressive matcher settings for candidate generation
        self.progressive_matcher.target_count = self.candidate_count
        
        # Logging callback for detailed logs
        self.log_callback = None
        self.session_id = None
    
    def find_recommendations(self, conversation_attributes: Dict[str, Any]) -> List[Product]:
        """
        Main method: Two-stage recommendation process
        
        Args:
            conversation_attributes: Output from conversation system with attributes,
                                   confidence_scores, and product_info
        
        Returns:
            Top 5 LLM-ranked products
        """
        # Log Stage 1 initiation
        if self.log_callback and self.session_id:
            self.log_callback(self.session_id, "recommendation_stage1", {
                "stage": "Stage 1: Progressive Filtering",
                "target_candidates": self.candidate_count,
                "filters_to_apply": list(conversation_attributes.get('attributes', {}).keys())
            })
        
        print(f"🎯 ENHANCED RECOMMENDATION SYSTEM")
        print(f"Stage 1: Finding {self.candidate_count} candidates...")
        
        # Pass logging info to progressive matcher
        if hasattr(self.progressive_matcher, 'log_callback'):
            self.progressive_matcher.log_callback = self.log_callback
            self.progressive_matcher.session_id = self.session_id
        
        # Stage 1: Get diverse candidate pool using progressive filtering
        candidates = self.progressive_matcher.find_recommendations(conversation_attributes)
        
        # Log Stage 1 completion
        if self.log_callback and self.session_id:
            self.log_callback(self.session_id, "recommendation_stage1", {
                "stage": "Stage 1 Complete",
                "candidates_found": len(candidates),
                "proceeding_to_stage2": len(candidates) > 5
            })
        
        print(f"✅ Stage 1 complete: Found {len(candidates)} candidates")
        
        # If we have 5 or fewer candidates, skip LLM ranking
        if len(candidates) <= 5:
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "Stage 2 Skipped",
                    "reason": f"Only {len(candidates)} candidates found",
                    "final_count": len(candidates)
                })
            print(f"⚡ Skipping LLM ranking (only {len(candidates)} candidates)")
            return candidates
        
        # Log Stage 2 initiation
        if self.log_callback and self.session_id:
            self.log_callback(self.session_id, "recommendation_stage2", {
                "stage": "Stage 2: LLM Ranking",
                "candidates_to_rank": len(candidates),
                "target_final_count": self.final_count
            })
        
        print(f"🧠 Stage 2: LLM ranking {len(candidates)} candidates to top {self.final_count}...")
        
        # Pass logging info to LLM ranker
        if hasattr(self.llm_ranker, 'log_callback'):
            self.llm_ranker.log_callback = self.log_callback
            self.llm_ranker.session_id = self.session_id
        
        # Stage 2: LLM intelligent ranking
        try:
            top_recommendations = self.llm_ranker.rank_candidates(
                candidates, 
                conversation_attributes
            )
            
            # Log Stage 2 completion
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "Stage 2 Complete",
                    "final_count": len(top_recommendations),
                    "llm_ranking_success": True
                })
            
            print(f"✅ Stage 2 complete: Selected top {len(top_recommendations)} recommendations")
            
            # Display ranking results if available
            self._display_ranking_results(top_recommendations)
            
            return top_recommendations
            
        except Exception as e:
            # Log Stage 2 failure
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "Stage 2 Failed",
                    "error": str(e),
                    "fallback_count": min(self.final_count, len(candidates))
                })
            
            print(f"❌ LLM ranking failed: {e}")
            print(f"🔄 Fallback: Returning first {self.final_count} candidates")
            return candidates[:self.final_count]
    
    def _display_ranking_results(self, ranked_products: List[Product]):
        """Display LLM ranking results for debugging"""
        print(f"\n🏆 LLM RANKING RESULTS:")
        for i, product in enumerate(ranked_products, 1):
            score = getattr(product, 'ranking_score', 'N/A')
            reasoning = getattr(product, 'ranking_reasoning', 'No reasoning provided')
            print(f"{i}. {product.name} - ${product.price} (Score: {score})")
            print(f"   Reasoning: {reasoning}")
            print()
    
    def get_candidate_details(self, conversation_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed information about the candidate selection process
        Useful for debugging and analysis
        """
        candidates = self.progressive_matcher.find_recommendations(conversation_attributes)
        
        return {
            'total_candidates': len(candidates),
            'candidates': [
                {
                    'name': p.name,
                    'price': p.price,
                    'category': p.category,
                    'fit': p.fit,
                    'color_or_print': p.color_or_print,
                    'fabric': p.fabric,
                    'occasion': p.occasion
                }
                for p in candidates
            ],
            'filters_applied': conversation_attributes.get('attributes', {}),
            'confidence_scores': conversation_attributes.get('confidence_scores', {}),
            'price_range': conversation_attributes.get('product_info', {}).get('price_range', {})
        }


class HybridMatcher:
    """
    Hybrid matcher that can switch between different strategies based on context
    """
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
        self.enhanced_matcher = EnhancedProgressiveMatcher(catalog)
        self.simple_matcher = ProgressiveMatcher(catalog)
    
    def find_recommendations(self, conversation_attributes: Dict[str, Any], 
                           use_llm_ranking: bool = True) -> List[Product]:
        """
        Find recommendations using the appropriate strategy
        
        Args:
            conversation_attributes: Conversation context
            use_llm_ranking: Whether to use LLM ranking (default: True)
        
        Returns:
            List of recommended products
        """
        if use_llm_ranking:
            return self.enhanced_matcher.find_recommendations(conversation_attributes)
        else:
            # Use simple progressive matcher with 5 results
            self.simple_matcher.target_count = 5
            return self.simple_matcher.find_recommendations(conversation_attributes)
    
    def compare_strategies(self, conversation_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare results from both strategies for analysis
        """
        print("🔍 COMPARING RECOMMENDATION STRATEGIES")
        
        # Get results from both strategies
        print("\n--- Simple Progressive Matching ---")
        self.simple_matcher.target_count = 5
        simple_results = self.simple_matcher.find_recommendations(conversation_attributes)
        
        print("\n--- Enhanced LLM Ranking ---")
        enhanced_results = self.enhanced_matcher.find_recommendations(conversation_attributes)
        
        return {
            'simple_strategy': [
                {'name': p.name, 'price': p.price, 'category': p.category}
                for p in simple_results
            ],
            'enhanced_strategy': [
                {
                    'name': p.name, 
                    'price': p.price, 
                    'category': p.category,
                    'ranking_score': getattr(p, 'ranking_score', 'N/A'),
                    'reasoning': getattr(p, 'ranking_reasoning', 'N/A')
                }
                for p in enhanced_results
            ]
        }
