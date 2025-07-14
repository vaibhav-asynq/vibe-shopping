"""
Vibe-to-Attribute Mapping Engine - Main Implementation

Contains three core components:
1. LLMExtractor - OpenAI integration for attribute extraction
2. RuleEnhancer - Fashion domain rule matching and enhancement
3. VibeToAttributeMapper - Main orchestrator combining LLM + Rules
"""

import json
import os
from typing import Dict, List, Any, Optional
import openai
from .models import (
    MappingResult, 
    AttributeExtractionResult,
    AttributeValue,
    PriceRange,
    VibeRule, 
    AttributeSchema
)


class LLMExtractor:
    """Handles OpenAI API integration for attribute extraction using structured output"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simplified prompt focusing on extraction logic since structure is enforced
        self.system_prompt = """You are a fashion expert AI that extracts structured attributes from natural language fashion queries.

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: User explicitly mentioned this attribute (e.g., "red dress" → color_or_print: 0.95)
- 0.7-0.9: Strong inference from vibe/context (e.g., "professional" → occasion: 0.85)
- 0.5-0.7: Logical inference but not certain (e.g., "party" → fit: 0.65)
- 0.3-0.5: Possible but weak inference (e.g., "cute" → color_or_print: 0.35)
- 0.1-0.3: Very uncertain guess

EXTRACTION PRIORITY:
1. HIGHEST: Extract attributes explicitly mentioned by user
2. MEDIUM: Interpret vibe/style words into attributes  
3. LOWEST: Infer additional attributes only if confident (>0.5)

PRICE EXTRACTION:
- Look for budget mentions: "under $100", "between $50-80", "cheap", "expensive"
- Extract specific product names or brands if mentioned
- Set confidence based on how explicit the price/product mention is

For each extracted attribute value, provide individual confidence scores.
Mark attributes as 'explicit' if directly mentioned, 'inferred' if derived from context."""

    def extract_attributes(self, query: str, schema: AttributeSchema) -> Optional[AttributeExtractionResult]:
        """Extract attributes from query using OpenAI structured output"""
        try:
            # Create user prompt with schema context
            user_prompt = f"""
AVAILABLE ATTRIBUTE VALUES:
{json.dumps(schema.get_all_attributes(), indent=2)}

USER QUERY: "{query}"

Extract fashion attributes, price preferences, and product details from this query.
Provide confidence scores for each extracted value and explain your reasoning.
"""
            
            # Call OpenAI API with structured output using beta client
            response = self.client.beta.chat.completions.parse(
                model=self.config['openai']['model'],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=AttributeExtractionResult,
                temperature=self.config['openai']['temperature'],
                max_tokens=self.config['openai']['max_tokens'],
                timeout=self.config['openai']['timeout_seconds']
            )
            
            # Get the parsed result directly from OpenAI
            if response.choices[0].message.parsed:
                return response.choices[0].message.parsed
            else:
                return None
            
        except openai.APITimeoutError:
            return None
        except openai.APIError:
            return None
        except Exception:
            return None


class RuleEnhancer:
    """Applies fashion domain rules to enhance and validate LLM output"""
    
    def __init__(self, rules_file_path: str):
        self.rules = self._load_rules(rules_file_path)
    
    def _load_rules(self, file_path: str) -> Dict[str, List[VibeRule]]:
        """Load vibe rules from JSON file"""
        with open(file_path, 'r') as f:
            rules_data = json.load(f)
        
        organized_rules = {}
        
        # Process each rule category
        for category, rules in rules_data.items():
            organized_rules[category] = []
            
            for rule_name, rule_data in rules.items():
                # Extract keywords from rule name and attributes
                keywords = [rule_name]
                
                # Add attribute values as potential keywords
                for attr_values in rule_data.get('fabric', []):
                    if isinstance(attr_values, list):
                        keywords.extend([v.lower() for v in attr_values])
                    else:
                        keywords.append(attr_values.lower())
                
                vibe_rule = VibeRule(
                    vibe_keywords=keywords,
                    target_attributes={k: v for k, v in rule_data.items() 
                                     if k not in ['confidence_boost', 'reasoning']},
                    confidence_boost=rule_data.get('confidence_boost', 0.5),
                    reasoning=rule_data.get('reasoning', f"Rule match for {rule_name}")
                )
                organized_rules[category].append(vibe_rule)
        
        return organized_rules
    
    def enhance_attributes(self, query: str, llm_attributes: Dict[str, Any]) -> tuple[Dict[str, Any], List[VibeRule]]:
        """Enhance LLM attributes with rule-based matching"""
        enhanced_attributes = llm_attributes.copy()
        applied_rules = []
        
        query_lower = query.lower()
        
        # Apply rules from all categories
        for category, rules in self.rules.items():
            for rule in rules:
                match_score = rule.matches_query(query)
                
                # Apply rule if it matches
                if match_score > 0:
                    applied_rules.append(rule)
                    
                    # Merge rule attributes
                    for attr_name, attr_values in rule.target_attributes.items():
                        if attr_name not in enhanced_attributes:
                            enhanced_attributes[attr_name] = []
                        
                        # Ensure we have a list
                        if not isinstance(enhanced_attributes[attr_name], list):
                            enhanced_attributes[attr_name] = [enhanced_attributes[attr_name]]
                        
                        # Add new values
                        if isinstance(attr_values, list):
                            for value in attr_values:
                                if value not in enhanced_attributes[attr_name]:
                                    enhanced_attributes[attr_name].append(value)
                        else:
                            if attr_values not in enhanced_attributes[attr_name]:
                                enhanced_attributes[attr_name].append(attr_values)
        
        return enhanced_attributes, applied_rules


class VibeToAttributeMapper:
    """Main orchestrator that combines LLM extraction with rule enhancement"""
    
    def __init__(self, config_file: str = "data/config.json", 
                 schema_file: str = "data/attribute_schema.json",
                 rules_file: str = "data/vibe_rules.json"):
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.schema = AttributeSchema.from_file(schema_file)
        self.llm_extractor = LLMExtractor(self.config)
        self.rule_enhancer = RuleEnhancer(rules_file)
    
    def map_vibe_to_attributes(self, query: str) -> MappingResult:
        """Main method to convert vibe query to structured attributes"""
        result = MappingResult(
            original_query=query,
            final_attributes={},
            overall_confidence=0.0
        )
        
        result.add_log(f"Processing query: '{query}'")
        
        # Stage 1: LLM Extraction with Pydantic structured output
        llm_extraction = self.llm_extractor.extract_attributes(query, self.schema)
        
        if llm_extraction:
            result.add_log("LLM extraction successful")
            result.llm_extraction = llm_extraction
            
            # Convert AttributeValue objects to simple dict for rule enhancement
            base_attributes = {}
            for attr_name in llm_extraction.get_attribute_names():
                attr_values = getattr(llm_extraction, attr_name)
                if attr_values:
                    base_attributes[attr_name] = [av.value for av in attr_values]
            
            base_confidence = llm_extraction.overall_confidence
        else:
            result.add_error("LLM extraction failed")
            result.add_log("Falling back to rule-based extraction only")
            base_attributes = {}
            base_confidence = 0.0
        
        # Stage 2: Rule Enhancement
        try:
            enhanced_attributes, applied_rules = self.rule_enhancer.enhance_attributes(
                query, base_attributes
            )
            result.rule_enhancements = applied_rules
            result.add_log(f"Applied {len(applied_rules)} matching rules")
            
            # Convert enhanced attributes back to AttributeValue format if we have LLM extraction
            if result.llm_extraction:
                # Boost confidence for rule-enhanced attributes
                for rule in applied_rules:
                    for attr_name in rule.target_attributes.keys():
                        if hasattr(result.llm_extraction, attr_name):
                            attr_values = getattr(result.llm_extraction, attr_name)
                            if attr_values:
                                for av in attr_values:
                                    # Boost confidence for values confirmed by rules
                                    if av.value in rule.target_attributes.get(attr_name, []):
                                        av.confidence = min(1.0, av.confidence + rule.confidence_boost * 0.15)
                
                # Add new attributes from rules as AttributeValue objects
                for attr_name, values in enhanced_attributes.items():
                    if not hasattr(result.llm_extraction, attr_name) or not getattr(result.llm_extraction, attr_name):
                        if attr_name in result.llm_extraction.get_attribute_names():
                            new_values = []
                            for value in values:
                                # Check if this value came from LLM or rules
                                if attr_name in base_attributes and value in base_attributes[attr_name]:
                                    continue  # Already handled above
                                else:
                                    # Find which rule added this value and use its confidence
                                    rule_confidence = 0.6  # Default fallback
                                    for rule in applied_rules:
                                        if attr_name in rule.target_attributes:
                                            rule_values = rule.target_attributes[attr_name]
                                            if isinstance(rule_values, list) and value in rule_values:
                                                rule_confidence = rule.confidence_boost
                                                break
                                            elif not isinstance(rule_values, list) and value == rule_values:
                                                rule_confidence = rule.confidence_boost
                                                break
                                    
                                    # New value from rules with rule's confidence
                                    new_values.append(AttributeValue(value=value, confidence=rule_confidence))
                            
                            if new_values:
                                existing_values = getattr(result.llm_extraction, attr_name) or []
                                setattr(result.llm_extraction, attr_name, existing_values + new_values)
            
            result.final_attributes = enhanced_attributes
            result.overall_confidence = result.llm_extraction.overall_confidence if result.llm_extraction else base_confidence
            
        except Exception as e:
            result.add_error(f"Rule enhancement failed: {str(e)}")
            result.final_attributes = base_attributes
            result.overall_confidence = base_confidence
        
        result.add_log("Mapping completed")
        return result
    
    def test_query(self, query: str) -> None:
        """Test a single query with detailed before/after analysis and scoring breakdown"""
        print(f"\n{'='*80}")
        print(f"🔍 TESTING QUERY: '{query}'")
        print(f"{'='*80}")
        
        result = self.map_vibe_to_attributes(query)
        
        # Step 1: Show LLM Extraction (Before Rules)
        print(f"\n📊 LLM EXTRACTION (Before Rules):")
        if result.llm_extraction:
            print(f"  🤖 Raw LLM Output:")
            
            # Show product name and price if extracted
            if result.llm_extraction.product_name:
                print(f"    🏷️  Product Name: {result.llm_extraction.product_name} (confidence: {result.llm_extraction.product_name_confidence:.2f})")
            
            if result.llm_extraction.price_range:
                pr = result.llm_extraction.price_range
                price_str = f"${pr.min_price or 0}-${pr.max_price or '∞'}"
                print(f"    💰 Price Range: {price_str} (confidence: {pr.confidence:.2f})")
            
            # Show original LLM attributes
            llm_attrs = {}
            for attr_name in result.llm_extraction.get_attribute_names():
                attr_values = getattr(result.llm_extraction, attr_name)
                if attr_values:
                    llm_attrs[attr_name] = attr_values
                    values_with_conf = []
                    avg_confidence = sum(av.confidence for av in attr_values) / len(attr_values)
                    confidence_emoji = "🟢" if avg_confidence >= 0.8 else "🟡" if avg_confidence >= 0.6 else "🔴"
                    
                    for av in attr_values:
                        values_with_conf.append(f"{av.value}({av.confidence:.2f})")
                    
                    print(f"    {confidence_emoji} {attr_name}: {', '.join(values_with_conf)}")
            
            print(f"  🎯 LLM Confidence: {result.llm_extraction.overall_confidence:.2f}")
            print(f"  💭 LLM Reasoning: {result.llm_extraction.reasoning}")
            
            if result.llm_extraction.explicit_attributes:
                print(f"  🎯 Explicit Attributes: {result.llm_extraction.explicit_attributes}")
            if result.llm_extraction.inferred_attributes:
                print(f"  🔍 Inferred Attributes: {result.llm_extraction.inferred_attributes}")
        else:
            print(f"  ❌ LLM extraction failed - using rule-based extraction only")
        
        # Step 2: Show Rule Matching and Application
        print(f"\n📋 RULE MATCHING:")
        if result.rule_enhancements:
            print(f"  ✅ Applied Rules ({len(result.rule_enhancements)} matched):")
            for i, rule in enumerate(result.rule_enhancements, 1):
                match_score = rule.matches_query(query)
                print(f"    {i}. \"{rule.reasoning}\" (match: {match_score:.2f}, boost: +{rule.confidence_boost:.2f})")
                
                # Show what this rule adds
                rule_additions = []
                for attr_name, attr_values in rule.target_attributes.items():
                    if isinstance(attr_values, list):
                        rule_additions.append(f"{attr_name}: {attr_values}")
                    else:
                        rule_additions.append(f"{attr_name}: [{attr_values}]")
                
                if rule_additions:
                    print(f"       → Adds: {', '.join(rule_additions)}")
        else:
            print(f"  ❌ No rules matched")
        
        # Step 3: Show Final Output (After Rules)
        print(f"\n📝 FINAL OUTPUT (After Rules):")
        print(f"  🎯 Enhanced Attributes:")
        
        if result.llm_extraction:
            # Show final attributes with source indicators
            for attr_name in result.llm_extraction.get_attribute_names():
                final_values = getattr(result.llm_extraction, attr_name)
                rule_values = result.final_attributes.get(attr_name, [])
                
                if final_values or rule_values:
                    # Determine source of each value
                    llm_values = [av.value for av in final_values] if final_values else []
                    all_values = set(llm_values + rule_values)
                    
                    value_sources = []
                    for value in all_values:
                        if value in llm_values:
                            # Find confidence from LLM
                            conf = next((av.confidence for av in final_values if av.value == value), 0.0)
                            if value in rule_values:
                                value_sources.append(f"{value}({conf:.2f})🔄")  # LLM + Rule enhanced
                            else:
                                value_sources.append(f"{value}({conf:.2f})🤖")  # LLM only
                        else:
                            # Find the actual confidence for rule-only values
                            rule_conf = 0.60  # Default fallback
                            if final_values:
                                for av in final_values:
                                    if av.value == value:
                                        rule_conf = av.confidence
                                        break
                            value_sources.append(f"{value}({rule_conf:.2f})📋")  # Rule only
                    
                    if value_sources:
                        avg_conf = sum(av.confidence for av in final_values) / len(final_values) if final_values else 0.6
                        confidence_emoji = "🟢" if avg_conf >= 0.8 else "🟡" if avg_conf >= 0.6 else "🔴"
                        print(f"    {confidence_emoji} {attr_name}: {', '.join(value_sources)}")
        else:
            # Fallback for rule-only extraction
            for attr, values in result.final_attributes.items():
                if values:
                    print(f"    📋 {attr}: {values} (rule-based)")
        
        print(f"  🏆 Final Confidence: {result.overall_confidence:.2f}")
        
        # Step 4: Show Confidence Changes
        if result.llm_extraction:
            initial_conf = result.llm_extraction.overall_confidence
            final_conf = result.overall_confidence
            change = final_conf - initial_conf
            change_emoji = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"\n📈 CONFIDENCE CHANGES:")
            print(f"  Overall: {initial_conf:.2f} → {final_conf:.2f} ({change_emoji}{abs(change):.2f})")
            
            if result.rule_enhancements:
                print(f"  Rule Impact: +{len(result.rule_enhancements)} rules applied")
        
        # Step 5: Show Processing Details
        if result.errors:
            print(f"\n❌ ERRORS:")
            for error in result.errors:
                print(f"  - {error}")
        
        print(f"\n📊 PROCESSING LOG:")
        for log in result.processing_log:
            print(f"  - {log}")
        
        # Legend
        print(f"\n🔤 LEGEND:")
        print(f"  🤖 LLM extracted  📋 Rule added  🔄 LLM + Rule enhanced")
        print(f"  🟢 High confidence (>0.8)  🟡 Medium (0.6-0.8)  🔴 Low (<0.6)")
