"""
Vibe-to-Attribute Mapping Engine

A two-stage hybrid system that translates natural language fashion queries 
into structured product attributes using LLM extraction and rule enhancement.
"""

from .vibe_mapper import VibeToAttributeMapper
from .models import MappingResult, AttributeExtractionResult, AttributeValue, PriceRange, VibeRule

__version__ = "1.0.0"
__all__ = ["VibeToAttributeMapper", "MappingResult", "AttributeExtractionResult", "AttributeValue", "PriceRange", "VibeRule"]
