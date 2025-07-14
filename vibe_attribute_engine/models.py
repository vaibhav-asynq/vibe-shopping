"""
Enhanced data models for the Vibe-to-Attribute Mapping Engine with Pydantic support
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field, validator
from enum import Enum
import json
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False




@dataclass
class VibeRule:
    """Simple fashion domain rule for vibe-to-attribute mapping"""
    vibe_keywords: List[str]
    target_attributes: Dict[str, Any]
    confidence_boost: float
    reasoning: str
    
    def matches_query(self, query: str) -> float:
        """Calculate how well this rule matches a query using fuzzy matching"""
        if not FUZZY_AVAILABLE:
            # Fallback to exact matching if fuzzywuzzy not available
            query_lower = query.lower()
            matches = 0
            for keyword in self.vibe_keywords:
                if keyword.lower() in query_lower:
                    matches += 1
            return matches / len(self.vibe_keywords) if self.vibe_keywords else 0.0
        
        query_lower = query.lower()
        matches = 0
        threshold = 80  # Increased threshold to reduce false positives
        
        for keyword in self.vibe_keywords:
            keyword_lower = keyword.lower()
            
            # Skip very short keywords to avoid false matches
            if len(keyword_lower) < 3:
                continue
            
            # Try fuzzy matching against the whole query
            whole_query_score = fuzz.partial_ratio(keyword_lower, query_lower)
            
            # Try fuzzy matching against individual words in the query
            word_scores = []
            for word in query_lower.split():
                # Skip very short words to avoid false matches like "i"
                if len(word) < 2:
                    continue
                    
                # Only use ratio for word-to-word matching to avoid substring issues
                ratio_score = fuzz.ratio(keyword_lower, word)
                
                # For partial matching, require minimum overlap
                if len(word) >= 3 and len(keyword_lower) >= 3:
                    partial_score = fuzz.partial_ratio(keyword_lower, word)
                    # Only use partial score if it's significantly higher than ratio
                    if partial_score > ratio_score + 20:
                        word_scores.append(partial_score)
                    else:
                        word_scores.append(ratio_score)
                else:
                    word_scores.append(ratio_score)
            
            best_word_score = max(word_scores) if word_scores else 0
            
            # Use the better of whole query or word matching (remove reverse matching)
            best_score = max(whole_query_score, best_word_score)
            
            if best_score >= threshold:
                matches += best_score / 100.0  # Convert to 0-1 scale
        
        return matches / len(self.vibe_keywords) if self.vibe_keywords else 0.0




@dataclass
class AttributeSchema:
    """Simple fashion attribute schema"""
    
    def __init__(self, schema_dict: Dict[str, List[str]]):
        self.schema = schema_dict
    
    @classmethod
    def from_file(cls, file_path: str) -> 'AttributeSchema':
        """Load schema from JSON file"""
        with open(file_path, 'r') as f:
            schema_dict = json.load(f)
        return cls(schema_dict)
    
    def get_all_attributes(self) -> Dict[str, List[str]]:
        """Get all attribute categories and their possible values"""
        return self.schema


@dataclass
class MappingResult:
    """Final result of the vibe-to-attribute mapping process"""
    original_query: str
    final_attributes: Dict[str, Any]
    overall_confidence: float
    llm_extraction: Optional['AttributeExtractionResult'] = None
    rule_enhancements: List[VibeRule] = field(default_factory=list)
    processing_log: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_log(self, message: str):
        """Add a processing log message"""
        self.processing_log.append(message)
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)


# ============================================================================
# PYDANTIC MODELS FOR OPENAI STRUCTURED OUTPUT
# ============================================================================

def create_enum_from_schema(attribute_name: str, schema_path: str = "data/attribute_schema.json") -> Type[Enum]:
    """Dynamically create enum from attribute schema"""
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    values = schema.get(attribute_name, [])
    
    # Create enum dynamically
    enum_dict = {}
    for value in values:
        # Convert to valid enum name (e.g., "Body hugging" -> "BODY_HUGGING")
        enum_name = value.upper().replace(" ", "_").replace("-", "_").replace("/", "_").replace("(", "").replace(")", "")
        # Handle special characters and ensure valid Python identifier
        enum_name = "".join(c if c.isalnum() or c == "_" else "_" for c in enum_name)
        # Remove multiple underscores
        while "__" in enum_name:
            enum_name = enum_name.replace("__", "_")
        enum_name = enum_name.strip("_")
        
        enum_dict[enum_name] = value
    
    return Enum(f"{attribute_name.title()}Type", enum_dict)


class AttributeValue(BaseModel):
    """Individual attribute value with confidence"""
    value: str = Field(description="The attribute value")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this specific value (0.0-1.0)")
    
    @classmethod
    def validate_against_schema(cls, attribute_name: str, value: str, schema_path: str = "data/attribute_schema.json") -> bool:
        """Validate that value exists in schema for given attribute"""
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            return value in schema.get(attribute_name, [])
        except (FileNotFoundError, json.JSONDecodeError):
            return False


class PriceRange(BaseModel):
    """Price range preferences with validation"""
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price preference in USD")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price preference in USD")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in price range extraction (0.0-1.0)")
    
    @validator('max_price')
    def max_greater_than_min(cls, v, values):
        """Ensure max_price is greater than min_price when both are provided"""
        if v is not None and values.get('min_price') is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v


class AttributeExtractionResult(BaseModel):
    """Complete structured output model for OpenAI parsing with comprehensive fashion query extraction"""
    
    # Product identification
    product_name: Optional[str] = Field(
        default=None, 
        description="Specific product name, brand, or model if explicitly mentioned by user"
    )
    product_name_confidence: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence in product name extraction (0.0-1.0)"
    )
    
    # Price preferences
    price_range: Optional[PriceRange] = Field(
        default=None, 
        description="Price range preferences extracted from budget mentions, price comparisons, etc."
    )
    
    # Fashion attributes with per-value confidence
    # Each attribute can have multiple values with individual confidence scores
    category: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Product category (top, dress, skirt, pants, etc.)"
    )
    fit: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="How the item fits (Relaxed, Body hugging, Tailored, etc.)"
    )
    fabric: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Fabric material (Linen, Silk, Cotton, etc.)"
    )
    color_or_print: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Color or print pattern (Red, Floral print, etc.)"
    )
    occasion: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Suitable occasions (Party, Work, Everyday, etc.)"
    )
    sleeve_length: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Sleeve style and length (Short sleeves, Sleeveless, etc.)"
    )
    neckline: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Neckline style (V neck, Round neck, etc.)"
    )
    length: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Garment length (Mini, Midi, Maxi, etc.)"
    )
    pant_type: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Pant style (Wide-legged, Skinny, etc.)"
    )
    sizes: Optional[List[AttributeValue]] = Field(
        default=None, 
        description="Size preferences (XS, S, M, L, XL, etc.)"
    )
    
    # Metadata and confidence tracking
    overall_confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Overall extraction confidence across all attributes (0.0-1.0)"
    )
    explicit_attributes: List[str] = Field(
        default_factory=list,
        description="List of attribute names that were explicitly mentioned by the user"
    )
    inferred_attributes: List[str] = Field(
        default_factory=list,
        description="List of attribute names that were inferred from context or vibe words"
    )
    reasoning: str = Field(
        description="Detailed explanation of extraction logic, confidence reasoning, and any assumptions made"
    )
    
    def get_attribute_names(self) -> List[str]:
        """Get list of all possible attribute names"""
        return [
            'category', 'fit', 'fabric', 'color_or_print', 'occasion',
            'sleeve_length', 'neckline', 'length', 'pant_type', 'sizes'
        ]
    
    def get_extracted_attributes(self) -> Dict[str, List[AttributeValue]]:
        """Get only attributes that have extracted values"""
        result = {}
        for attr_name in self.get_attribute_names():
            attr_value = getattr(self, attr_name)
            if attr_value is not None and len(attr_value) > 0:
                result[attr_name] = attr_value
        return result
    
    def get_high_confidence_values(self, threshold: float = 0.7) -> Dict[str, List[AttributeValue]]:
        """Get only attribute values with confidence above threshold"""
        result = {}
        for attr_name, values in self.get_extracted_attributes().items():
            high_conf_values = [v for v in values if v.confidence >= threshold]
            if high_conf_values:
                result[attr_name] = high_conf_values
        return result
    
    def validate_against_schema(self, schema_path: str = "data/attribute_schema.json") -> Dict[str, List[str]]:
        """Validate all extracted values against the attribute schema"""
        invalid_values = {}
        
        for attr_name, values in self.get_extracted_attributes().items():
            invalid_for_attr = []
            for attr_value in values:
                if not AttributeValue.validate_against_schema(attr_name, attr_value.value, schema_path):
                    invalid_for_attr.append(attr_value.value)
            
            if invalid_for_attr:
                invalid_values[attr_name] = invalid_for_attr
        
        return invalid_values


class AttributeSchemaManager:
    """Manages dynamic loading and validation of attribute schema"""
    
    def __init__(self, schema_path: str = "data/attribute_schema.json"):
        self.schema_path = schema_path
        self._schema_cache = None
        self._enum_cache = {}
    
    def load_schema(self) -> Dict[str, List[str]]:
        """Load schema from JSON file with caching"""
        if self._schema_cache is None:
            with open(self.schema_path, 'r') as f:
                self._schema_cache = json.load(f)
        return self._schema_cache
    
    def get_attribute_values(self, attribute_name: str) -> List[str]:
        """Get possible values for a specific attribute"""
        schema = self.load_schema()
        return schema.get(attribute_name, [])
    
    def get_attribute_enum(self, attribute_name: str) -> Type[Enum]:
        """Get or create enum for attribute with caching"""
        if attribute_name not in self._enum_cache:
            self._enum_cache[attribute_name] = create_enum_from_schema(attribute_name, self.schema_path)
        return self._enum_cache[attribute_name]
    
    def validate_value(self, attribute_name: str, value: str) -> bool:
        """Validate that a value is valid for the given attribute"""
        return value in self.get_attribute_values(attribute_name)
    
    def get_all_attribute_names(self) -> List[str]:
        """Get list of all attribute names in schema"""
        schema = self.load_schema()
        return list(schema.keys())


# Global schema manager instance
schema_manager = AttributeSchemaManager()
