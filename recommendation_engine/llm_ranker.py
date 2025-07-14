"""
LLM-powered intelligent ranking for product recommendations
"""
import json
import os
from typing import List, Dict, Any, Tuple
import openai
from .models import Product


class LLMRanker:
    """Uses LLM to intelligently rank product candidates based on user context"""
    
    def __init__(self, config_file: str = "data/config.json"):
        """Initialize the LLM ranker"""
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Logging callback for detailed logs
        self.log_callback = None
        self.session_id = None
    
    def rank_candidates(self, candidates: List[Product], conversation_context: Dict[str, Any]) -> List[Product]:
        """
        Use LLM to intelligently rank candidates and return top 5
        
        Args:
            candidates: List of candidate products (up to 15)
            conversation_context: Full conversation context including attributes, history, etc.
        
        Returns:
            Top 5 ranked products
        """
        # Log Stage 2 initiation
        if self.log_callback and self.session_id:
            self.log_callback(self.session_id, "recommendation_stage2", {
                "stage": "LLM Ranking Started",
                "candidates_to_rank": len(candidates),
                "ranking_criteria": ["relevance", "style_coherence", "value", "variety"]
            })
        
        if len(candidates) <= 5:
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "LLM Ranking Skipped",
                    "reason": "5 or fewer candidates",
                    "returning_all": len(candidates)
                })
            return candidates
        
        # Log prompt preparation
        if self.log_callback and self.session_id:
            original_query = conversation_context.get('original_query', '')
            attributes = conversation_context.get('attributes', {})
            self.log_callback(self.session_id, "recommendation_stage2", {
                "stage": "Building LLM Prompt",
                "original_query": original_query,
                "user_attributes": list(attributes.keys()),
                "candidate_count": len(candidates)
            })
        
        # Prepare data for LLM
        prompt = self._build_ranking_prompt(candidates, conversation_context)
        
        try:
            # Log LLM call
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "Calling LLM for Ranking",
                    "model": self.config['openai']['model'],
                    "temperature": 0.3
                })
            
            # Get LLM ranking
            ranking_result = self._call_llm_for_ranking(prompt)
            
            # Log LLM response
            if self.log_callback and self.session_id:
                overall_reasoning = ranking_result.get('overall_reasoning', 'No reasoning provided')
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "LLM Ranking Response",
                    "overall_reasoning": overall_reasoning,
                    "top_selections": len(ranking_result.get('top_5', []))
                })
            
            # Parse and return ranked products
            ranked_products = self._parse_ranking_result(ranking_result, candidates)
            
            # Log final ranking results
            if self.log_callback and self.session_id:
                product_details = []
                for i, product in enumerate(ranked_products[:5], 1):
                    score = getattr(product, 'ranking_score', 'N/A')
                    reasoning = getattr(product, 'ranking_reasoning', 'No reasoning')
                    product_details.append({
                        "rank": i,
                        "name": product.name,
                        "price": product.price,
                        "score": score,
                        "reasoning": reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                    })
                
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "LLM Ranking Complete",
                    "final_recommendations": len(ranked_products),
                    "product_rankings": product_details
                })
            
            return ranked_products[:5]
            
        except Exception as e:
            # Log ranking failure
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "recommendation_stage2", {
                    "stage": "LLM Ranking Failed",
                    "error": str(e),
                    "fallback_count": min(5, len(candidates))
                })
            
            print(f"LLM ranking error: {e}")
            # Fallback: return first 5 candidates
            return candidates[:5]
    
    def _build_ranking_prompt(self, candidates: List[Product], context: Dict[str, Any]) -> str:
        """Build the ranking prompt for LLM"""
        
        # Extract context information
        original_query = context.get('original_query', 'fashion item')
        attributes = context.get('attributes', {})
        price_info = context.get('product_info', {}).get('price_range', {})
        conversation_history = context.get('conversation_history', [])
        
        # Format conversation history
        history_text = "\n".join(conversation_history[-4:]) if conversation_history else "None"
        
        # Format price information
        price_text = "No specific budget mentioned"
        if price_info:
            min_p = price_info.get('min_price')
            max_p = price_info.get('max_price')
            if max_p:
                price_text = f"Budget: up to ${max_p}"
            elif min_p:
                price_text = f"Budget: at least ${min_p}"
        
        # Format candidate products
        candidates_text = ""
        for i, product in enumerate(candidates, 1):
            candidates_text += f"{i}. **{product.name}** - ${product.price}\n"
            candidates_text += f"   Category: {product.category} | Fit: {product.fit} | Color: {product.color_or_print}\n"
            if product.fabric:
                candidates_text += f"   Fabric: {product.fabric}"
            if product.occasion:
                candidates_text += f" | Occasion: {product.occasion}"
            if product.neckline:
                candidates_text += f" | Neckline: {product.neckline}"
            candidates_text += f"\n   Sizes: {', '.join(product.available_sizes)}\n\n"
        
        prompt = f"""You are an expert fashion stylist helping a customer find the perfect items. 

USER CONTEXT:
- Original Request: "{original_query}"
- Stated Preferences: {json.dumps(attributes, indent=2)}
- {price_text}
- Recent Conversation: {history_text}

CANDIDATE PRODUCTS:
{candidates_text}

TASK: Select the TOP 5 products that best match this customer's needs. Consider:

RANKING CRITERIA:
1. **Relevance (40%)**: How well does the product match their stated preferences?
2. **Style Coherence (25%)**: Does it fit the overall vibe/occasion they mentioned?
3. **Value (20%)**: Is it appropriately priced for what they're looking for?
4. **Variety (15%)**: Ensure the final 5 offer good options diversity

RESPONSE FORMAT (JSON only):
{{
  "top_5": [
    {{
      "product_number": 1,
      "product_name": "Product Name",
      "ranking_score": 95,
      "reasoning": "Brief explanation of why this is perfect for them"
    }},
    ...
  ],
  "overall_reasoning": "Brief explanation of the selection strategy"
}}

Respond with JSON only:"""
        
        return prompt
    
    def _call_llm_for_ranking(self, prompt: str) -> Dict[str, Any]:
        """Call LLM to get ranking decision"""
        
        response = self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=[
                {"role": "system", "content": "You are a helpful fashion stylist assistant that responds with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent ranking
            max_tokens=800,
            timeout=self.config['openai']['timeout_seconds']
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response if needed
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        # Parse JSON response
        ranking_result = json.loads(response_text)
        
        return ranking_result
    
    def _parse_ranking_result(self, ranking_result: Dict[str, Any], candidates: List[Product]) -> List[Product]:
        """Parse LLM ranking result and return ordered products"""
        
        ranked_products = []
        
        try:
            top_5 = ranking_result.get('top_5', [])
            
            for item in top_5:
                product_number = item.get('product_number', 1)
                # Convert to 0-based index
                index = product_number - 1
                
                if 0 <= index < len(candidates):
                    product = candidates[index]
                    # Add ranking metadata to product (optional)
                    if hasattr(product, '__dict__'):
                        product.ranking_score = item.get('ranking_score', 0)
                        product.ranking_reasoning = item.get('reasoning', '')
                    ranked_products.append(product)
            
            # If we don't have 5 products, fill with remaining candidates
            used_indices = set()
            for item in top_5:
                used_indices.add(item.get('product_number', 1) - 1)
            
            for i, candidate in enumerate(candidates):
                if i not in used_indices and len(ranked_products) < 5:
                    ranked_products.append(candidate)
            
            return ranked_products
            
        except Exception as e:
            print(f"Error parsing ranking result: {e}")
            return candidates[:5]
