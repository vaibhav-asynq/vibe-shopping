"""
Data models for the recommendation engine
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Product:
    """Product data model matching the Excel structure"""
    id: str
    name: str
    category: str
    available_sizes: List[str]
    fit: Optional[str]
    fabric: Optional[str]
    sleeve_length: Optional[str]
    color_or_print: Optional[str]
    occasion: Optional[str]
    neckline: Optional[str]
    length: Optional[str]
    pant_type: Optional[str]
    price: float
    
    def matches_size(self, size: str) -> bool:
        """Check if product is available in the given size"""
        return size in self.available_sizes
    
    def matches_price_range(self, min_price: float = None, max_price: float = None) -> bool:
        """Check if product price falls within the given range"""
        if min_price and self.price < min_price:
            return False
        if max_price and self.price > max_price:
            return False
        return True


@dataclass
class AttributeFilter:
    """Filter for product attributes with confidence"""
    name: str
    values: List[str]
    confidence: float


@dataclass
class PriceFilter:
    """Filter for price range with confidence"""
    min_price: Optional[float]
    max_price: Optional[float]
    confidence: float
    name: str = "price"  # Add name attribute for consistency
