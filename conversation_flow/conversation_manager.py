"""
Simplified LLM-Driven Conversation Flow Manager for Fashion Chatbot

Uses LLM to make all conversation decisions through dynamic prompts,
avoiding hardcoded logic and keeping the code minimal and flexible.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
import openai
from .models import ConversationState, ConversationTurn, ConversationPhase

# Add parent directory to path for vibe mapper import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vibe_attribute_engine import VibeToAttributeMapper


class SimplifiedConversationManager:
    """
    LLM-driven conversation manager that uses dynamic prompts to handle
    all conversation logic without hardcoded rules.
    
    Key features:
    - Single dynamic prompt system
    - LLM makes all decisions (what to ask, when to proceed, how to respond)
    - Minimal state tracking
    - Natural conversational responses
    - Flexible and easy to modify through prompt updates
    """
    
    def __init__(self, config_file: str = "data/config.json"):
        """Initialize the simplified conversation manager"""
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize vibe mapper for attribute extraction
        self.vibe_mapper = VibeToAttributeMapper(config_file)
        
        # Logging callback for detailed logs
        self.log_callback = None
        
        # Single dynamic prompt template
        self.dynamic_prompt = """You are a friendly personal shopping assistant helping users find perfect fashion items.

CONTEXT:
- Original Query: "{original_query}"
- Current Attributes: {attributes}
- Conversation History: {history}
- User Input: "{user_input}"
- Questions Asked: {questions_asked}/2
- Current Phase: {current_phase}

TASK: Analyze the conversation and decide the next action. Respond with valid JSON only:

{{
  "action": "ask_question" | "ready_for_recommendations" | "handle_changes",
  "response_message": "Your natural, conversational response",
  "next_phase": "gathering_info" | "ready_for_recommendations" | "handling_changes",
  "reasoning": "Brief explanation of your decision"
}}

DECISION RULES:
- STRICT LIMIT: Maximum 2 questions allowed for gathering info
- If missing size OR category AND questions_asked < 2: choose "ask_question" 
- If have both size AND category OR questions_asked >= 2: choose "ready_for_recommendations"
- If user wants changes after seeing recommendations: choose "handle_changes"
- NEVER exceed 2 questions - proceed to recommendations after 2 questions regardless
- Always reference their original style/vibe when possible
- Keep responses warm, enthusiastic, and helpful
- Be conversational and natural

SPECIAL INSTRUCTION FOR RECOMMENDATIONS:
When action is "ready_for_recommendations", your response_message should be a thoughtful explanation of WHY you selected these recommendations based on their preferences, style, and needs. Explain your reasoning for the choices without listing specific product names. Focus on how the selections match their original query, style preferences, occasion needs, size requirements, etc. Make it personal and insightful.

EXAMPLES:
- Ask question: "Love the brunch vibe! What size should I look for?"
- Ready for recs: "Perfect! Based on your need for polished client meeting attire in size L, I've selected pieces that balance professionalism with modern style. These options work beautifully for work occasions and stay within your budget, focusing on versatile pieces that can transition from boardroom to networking events."
- Handle changes: "I totally get that! Let me find some more formal options for you."

Respond with JSON only:"""

    def build_prompt(self, state: ConversationState, user_input: str = "") -> str:
        """Build dynamic prompt with current conversation context"""
        
        # Format conversation history (last 4 messages for context)
        history_text = "\n".join(state.conversation_history[-4:]) if state.conversation_history else "None"
        
        # Format attributes
        attributes_text = json.dumps(state.all_attributes, indent=2) if state.all_attributes else "None"
        
        return self.dynamic_prompt.format(
            original_query=state.original_query,
            attributes=attributes_text,
            history=history_text,
            user_input=user_input,
            questions_asked=state.questions_asked,
            current_phase=state.phase.value
        )

    def call_llm_for_decision(self, prompt: str) -> Dict[str, Any]:
        """Call LLM to make conversation decision"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that responds with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200,
                timeout=self.config['openai']['timeout_seconds']
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up response if needed
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            # Parse JSON response
            decision = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["action", "response_message", "next_phase", "reasoning"]
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Missing required field: {field}")
            
            return decision
            
        except Exception as e:
            print(f"LLM decision error: {e}")
            # Fallback decision
            return self._get_fallback_decision()

    def _get_fallback_decision(self) -> Dict[str, Any]:
        """Fallback decision when LLM fails"""
        
        return {
            "action": "ask_question",
            "response_message": "What size should I look for, and are you thinking dresses, tops, or bottoms?",
            "next_phase": "gathering_info",
            "reasoning": "Fallback: LLM error, asking for essential info"
        }

    def get_recommendations(self, state: ConversationState) -> List[Any]:
        """Get product recommendations based on conversation state"""
        try:
            from recommendation_engine import ProductCatalog, EnhancedProgressiveMatcher
            
            catalog = ProductCatalog()
            matcher = EnhancedProgressiveMatcher(catalog)
            
            # Set up logging for recommendation engine
            session_id = getattr(state, 'session_id', None)
            if self.log_callback and session_id:
                matcher.log_callback = self.log_callback
                matcher.session_id = session_id
            
            # Add conversation context for LLM ranking
            enhanced_attributes = state.all_attributes.copy()
            enhanced_attributes['original_query'] = state.original_query
            enhanced_attributes['conversation_history'] = state.conversation_history
            
            # Use the enhanced two-stage system
            recommendations = matcher.find_recommendations(enhanced_attributes)
            return recommendations
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            if self.log_callback and session_id:
                self.log_callback(session_id, "error", {"message": f"Recommendation engine failed: {str(e)}"})
            return []

    def format_recommendations(self, products: List[Any]) -> str:
        """Format product recommendations for user display"""
        if not products:
            return "I couldn't find exact matches, but let me broaden the search for you!"
        
        response = f"I found {len(products)} perfect matches for you!\n\n"
        for i, product in enumerate(products[:3], 1):
            response += f"{i}. **{product.name}** - ${product.price}\n"
            response += f"   {product.category.title()} | {product.fit} | {product.color_or_print}\n"
            if product.fabric:
                response += f"   Fabric: {product.fabric}\n"
            if product.available_sizes:
                response += f"   Available sizes: {', '.join(product.available_sizes)}\n"
            response += "\n"
        
        if len(products) > 3:
            response += f"...and {len(products) - 3} more great options!\n\n"
        
        response += "What do you think? Would you like to see more options or make any changes?"
        return response

    def extract_attributes_from_input(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Enhanced extraction using new vibe mapper with confidence scores and product info"""
        
        try:
            # Use enhanced vibe mapper
            result = self.vibe_mapper.map_vibe_to_attributes(user_input)
            
            enhanced_attributes = {
                'attributes': {},
                'confidence_scores': {},
                'product_info': {},
                'extraction_quality': result.overall_confidence,
                'rule_count': len(result.rule_enhancements) if result.rule_enhancements else 0
            }
            
            # Extract attributes with confidence from LLM extraction ONLY
            if result.llm_extraction:
                for attr_name in result.llm_extraction.get_attribute_names():
                    attr_values = getattr(result.llm_extraction, attr_name)
                    if attr_values:
                        # Store values and their confidence scores
                        enhanced_attributes['attributes'][attr_name] = [av.value for av in attr_values]
                        enhanced_attributes['confidence_scores'][attr_name] = [av.confidence for av in attr_values]
                
                # Extract product information
                if result.llm_extraction.product_name:
                    enhanced_attributes['product_info']['name'] = result.llm_extraction.product_name
                    enhanced_attributes['product_info']['name_confidence'] = result.llm_extraction.product_name_confidence
                
                if result.llm_extraction.price_range:
                    pr = result.llm_extraction.price_range
                    # Only store if we have at least one numeric value
                    if pr.min_price is not None or pr.max_price is not None:
                        enhanced_attributes['product_info']['price_range'] = {
                            'min_price': pr.min_price,
                            'max_price': pr.max_price,
                            'confidence': pr.confidence
                        }
            
            # Log detailed extraction results if callback is available
            if self.log_callback and session_id:
                self.log_callback(session_id, "attribute_extraction", enhanced_attributes)
            
            print(f"DEBUG: Enhanced extraction result: {enhanced_attributes}")
            return enhanced_attributes
            
        except Exception as e:
            print(f"Enhanced attribute extraction error: {e}")
            if self.log_callback and session_id:
                self.log_callback(session_id, "error", {"message": f"Attribute extraction failed: {str(e)}"})
            return {}

    def process_conversation(self, user_input: str, state: ConversationState) -> ConversationTurn:
        """
        Main method to process conversation turn using LLM decisions.
        
        Args:
            user_input: User's input (empty string for first turn)
            state: Current conversation state
            
        Returns:
            ConversationTurn with LLM-generated response and next action
        """
        
        # Extract attributes from user input if provided
        if user_input.strip():
            # Get session_id from state if available
            session_id = getattr(state, 'session_id', None)
            extracted_attrs = self.extract_attributes_from_input(user_input, session_id)
            
            # Merge attributes properly, preserving existing ones
            for key, value in extracted_attrs.items():
                if key == 'attributes':
                    # Merge attribute dictionaries
                    if 'attributes' not in state.all_attributes:
                        state.all_attributes['attributes'] = {}
                    state.all_attributes['attributes'].update(value)
                elif key == 'confidence_scores':
                    # Merge confidence scores
                    if 'confidence_scores' not in state.all_attributes:
                        state.all_attributes['confidence_scores'] = {}
                    state.all_attributes['confidence_scores'].update(value)
                else:
                    # For other keys, just update
                    state.all_attributes[key] = value
            
            state.add_to_history(f"User: {user_input}")
        
        # Auto-transition from ready_for_recommendations to handling_changes after showing recommendations once
        if state.phase == ConversationPhase.READY_FOR_RECOMMENDATIONS and user_input.strip():
            print("DEBUG: Auto-transitioning from recommendations to handling changes")
            return ConversationTurn.create(
                action="handle_changes",
                phase=ConversationPhase.HANDLING_CHANGES,
                response_message="How do these look? Let me know if you'd like to see anything different!",
                reasoning="Auto-transition: Moving to handle changes after showing recommendations",
                next_phase=ConversationPhase.HANDLING_CHANGES
            )

        # Build dynamic prompt with current context
        prompt = self.build_prompt(state, user_input)
        
        # Get LLM decision
        decision = self.call_llm_for_decision(prompt)
        
        # Log LLM decision details if callback is available
        session_id = getattr(state, 'session_id', None)
        if self.log_callback and session_id:
            self.log_callback(session_id, "llm_decision", {
                "reasoning": decision.get("reasoning"),
                "action": decision.get("action"),
                "next_phase": decision.get("next_phase")
            })
        
        # Update state based on decision
        response_message = decision["response_message"]
        next_phase = ConversationPhase(decision["next_phase"])
        action = decision["action"]
        
        # Safety validation: Ensure LLM respects question limits
        if action == "ask_question" and state.questions_asked >= 2:
            print("DEBUG: LLM tried to ask question after limit, forcing recommendations")
            action = "ready_for_recommendations"
            next_phase = ConversationPhase.READY_FOR_RECOMMENDATIONS
            response_message = "Perfect! Let me show you some great options based on what we've discussed!"
        
        # Get recommendations if action is ready_for_recommendations
        recommendations = None
        if action == "ready_for_recommendations":
            recommendations = self.get_recommendations(state)
            if not recommendations:
                response_message = "I'm having trouble finding matches right now. Could you tell me a bit more about what you're looking for?"
            # If we have recommendations, the LLM already provided the explanation in response_message
            # We don't need to override it with format_recommendations
        
        # Update conversation state
        if action == "ask_question":
            state.questions_asked += 1
        
        state.phase = next_phase
        state.add_to_history(f"Assistant: {response_message}")
        
        # Create and return conversation turn
        return ConversationTurn.create(
            action=action,
            phase=next_phase,
            response_message=response_message,
            reasoning=decision["reasoning"],
            next_phase=next_phase,
            recommendations=recommendations
        )

    # Legacy compatibility methods
    def process_conversation_turn(self, user_input: str, existing_attributes: Dict[str, Any], 
                                conversation_state: ConversationState) -> ConversationTurn:
        """Legacy method for backward compatibility"""
        
        # Merge existing attributes into state
        conversation_state.all_attributes.update(existing_attributes)
        
        # Use new simplified method
        return self.process_conversation(user_input, conversation_state)

    def find_missing_attributes(self, existing_attributes: Dict[str, Any]) -> List[str]:
        """Legacy method for backward compatibility"""
        missing = []
        
        if 'size' not in existing_attributes or not existing_attributes['size']:
            missing.append('size')
        if 'category' not in existing_attributes or not existing_attributes['category']:
            missing.append('category')
        
        return missing


# Aliases for backward compatibility
EnhancedConversationManager = SimplifiedConversationManager
SimpleConversationManager = SimplifiedConversationManager
