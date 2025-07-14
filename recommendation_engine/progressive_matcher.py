"""
Progressive confidence-based product matching
"""
import traceback
from typing import List, Dict, Any, Union
from .models import Product, AttributeFilter, PriceFilter
from .catalog import ProductCatalog


class ProgressiveMatcher:
    """Progressive filtering system that relaxes constraints based on confidence"""
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
        self.confidence_threshold = 0.6  # Strategy 3: Filter out low-confidence values
        self.target_count = 8  # Target number of recommendations
        
        # Logging callback for detailed logs
        self.log_callback = None
        self.session_id = None
    
    def find_recommendations(self, conversation_attributes: Dict[str, Any]) -> List[Product]:
        """
        Main method: Find product recommendations using progressive filtering
        
        Args:
            conversation_attributes: Output from conversation system with attributes,
                                   confidence_scores, and product_info
        
        Returns:
            List of recommended products
        """
        print(f"Finding recommendations for: {conversation_attributes}")
        
        # Step 1: Prepare filters using Strategy 3 (confidence threshold)
        filters = self.prepare_filters(conversation_attributes)
        print(f"Prepared {len(filters)} filters")
        
        # Step 2: Apply Strategy 4 (progressive removal)
        recommendations = self.apply_progressive_filtering(filters)
        
        return recommendations
    
    def prepare_filters(self, attributes: Dict[str, Any]) -> List[Union[AttributeFilter, PriceFilter]]:
        """
        Strategy 3: Prepare filters with confidence threshold filtering
        """
        filters = []
        
        print(f"DEBUG: prepare_filters called with attributes: {attributes}")
        
        try:
            # Process attribute filters
            attributes_dict = attributes.get('attributes', {})
            print(f"DEBUG: attributes_dict: {attributes_dict}")
            
            for attr_name, values in attributes_dict.items():
                try:
                    print(f"DEBUG: Processing attribute '{attr_name}' with values: {values} (type: {type(values)})")
                    
                    # Check if values is actually a list
                    if not isinstance(values, list):
                        print(f"ERROR: values for {attr_name} is not a list! Type: {type(values)}, Value: {values}")
                        # Convert to list if it's not
                        values = [values] if values is not None else []
                        print(f"DEBUG: Converted to list: {values}")
                    
                    # Get confidence scores
                    confidence_scores_dict = attributes.get('confidence_scores', {})
                    print(f"DEBUG: confidence_scores_dict: {confidence_scores_dict}")
                    
                    confidences = confidence_scores_dict.get(attr_name, [1.0] * len(values))
                    print(f"DEBUG: confidences for {attr_name}: {confidences} (type: {type(confidences)})")
                    
                    # Apply confidence threshold
                    filtered_values = []
                    filtered_confidences = []
                    
                    for value, conf in zip(values, confidences):
                        print(f"DEBUG: Processing value '{value}' with confidence {conf}")
                        if conf >= self.confidence_threshold:
                            filtered_values.append(value)
                            filtered_confidences.append(conf)
                    
                    # Fallback if nothing meets threshold
                    if not filtered_values:
                        print(f"DEBUG: No values met threshold, using highest confidence")
                        max_idx = confidences.index(max(confidences))
                        filtered_values = [values[max_idx]]
                        filtered_confidences = [confidences[max_idx]]
                    
                    print(f"DEBUG: Final filtered_values: {filtered_values}")
                    print(f"DEBUG: Final filtered_confidences: {filtered_confidences}")
                    
                    # Create filter with average confidence
                    avg_confidence = sum(filtered_confidences) / len(filtered_confidences)
                    print(f"DEBUG: Creating AttributeFilter for {attr_name}")
                    
                    filter_obj = AttributeFilter(
                        name=attr_name,
                        values=filtered_values,
                        confidence=avg_confidence
                    )
                    filters.append(filter_obj)
                    
                    print(f"Filter {attr_name}: {filtered_values} (confidence: {avg_confidence:.2f})")
                    
                except Exception as e:
                    print(f"ERROR: Processing attribute {attr_name}: {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
                    print(f"ERROR: values: {values}, confidences: {confidences}")
            
            # Add price filter
            print(f"DEBUG: Processing price filter")
            price_info = attributes.get('product_info', {}).get('price_range')
            print(f"DEBUG: price_info: {price_info}")
            
            if price_info:
                try:
                    print(f"DEBUG: Creating PriceFilter")
                    price_filter = PriceFilter(
                        min_price=price_info.get('min_price'),
                        max_price=price_info.get('max_price'),
                        confidence=price_info.get('confidence', 1.0)
                    )
                    filters.append(price_filter)
                    print(f"Price filter: ${price_info.get('min_price', 0)}-${price_info.get('max_price', '∞')} (confidence: {price_info.get('confidence', 1.0):.2f})")
                except Exception as e:
                    print(f"ERROR: Creating price filter: {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
            
            print(f"DEBUG: prepare_filters completed successfully with {len(filters)} filters")
            return filters
            
        except Exception as e:
            print(f"ERROR: Fatal error in prepare_filters: {e}")
            print(f"ERROR: Full traceback:")
            print(traceback.format_exc())
            return []
    
    def apply_progressive_filtering(self, filters: List[Union[AttributeFilter, PriceFilter]]) -> List[Product]:
        """
        Strategy 4: Progressive filter removal based on confidence
        """
        print(f"DEBUG: apply_progressive_filtering called with {len(filters)} filters")
        
        try:
            # Debug each filter before sorting
            for i, f in enumerate(filters):
                print(f"DEBUG: Filter {i}: {f.name} (confidence: {f.confidence}, type: {type(f)})")
                print(f"DEBUG: Filter {i} values: {getattr(f, 'values', 'N/A')}")
            
            print(f"DEBUG: About to sort filters by confidence")
            # Sort filters by confidence (lowest first for removal)
            sorted_filters = sorted(filters, key=lambda f: f.confidence)
            print(f"DEBUG: Filters sorted successfully")
            
            print(f"DEBUG: About to copy sorted filters")
            active_filters = sorted_filters.copy()
            print(f"DEBUG: Filters copied successfully, active_filters count: {len(active_filters)}")
            
            # Log initial filter setup
            if self.log_callback and self.session_id:
                try:
                    print(f"DEBUG: About to create filter_names list")
                    filter_names = [f.name for f in active_filters]
                    print(f"DEBUG: filter_names created: {filter_names}")
                    
                    self.log_callback(self.session_id, "recommendation_stage1", {
                        "filters_applied": len(active_filters),
                        "filter_names": filter_names,
                        "target_count": self.target_count
                    })
                    print(f"DEBUG: Logging callback completed")
                except Exception as e:
                    print(f"ERROR: Logging callback failed: {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
            
            print(f"Starting progressive filtering with {len(active_filters)} filters")
            
            relaxation_steps = []
            
            while True:
                try:
                    print(f"DEBUG: About to apply filters, active_filters count: {len(active_filters)}")
                    # Apply current filters
                    results = self.apply_filters(active_filters)
                    print(f"DEBUG: apply_filters completed, results count: {len(results)}")
                    
                    # Log current filtering results
                    if self.log_callback and self.session_id:
                        try:
                            self.log_callback(self.session_id, "recommendation_stage1", {
                                "active_filters": len(active_filters),
                                "candidates_found": len(results),
                                "target_reached": len(results) >= self.target_count
                            })
                        except Exception as e:
                            print(f"ERROR: Logging callback failed: {e}")
                    
                    print(f"With {len(active_filters)} filters: {len(results)} products found")
                    
                    # Check if we have enough results
                    if len(results) >= self.target_count:
                        # Log successful completion
                        if self.log_callback and self.session_id:
                            try:
                                self.log_callback(self.session_id, "recommendation_stage1", {
                                    "stage": "Progressive Filtering Complete",
                                    "final_candidates": len(results),
                                    "relaxation_steps": relaxation_steps,
                                    "filters_remaining": len(active_filters)
                                })
                            except Exception as e:
                                print(f"ERROR: Logging callback failed: {e}")
                        
                        print(f"Target reached! Returning {len(results[:self.target_count])} products")
                        return results[:self.target_count]
                    
                    # If no more filters to remove, return what we have
                    if not active_filters:
                        # Log completion with insufficient results
                        if self.log_callback and self.session_id:
                            try:
                                self.log_callback(self.session_id, "recommendation_stage1", {
                                    "stage": "Progressive Filtering Complete (Insufficient Results)",
                                    "final_candidates": len(results),
                                    "relaxation_steps": relaxation_steps,
                                    "all_filters_relaxed": True
                                })
                            except Exception as e:
                                print(f"ERROR: Logging callback failed: {e}")
                        
                        print(f"No more filters to remove. Returning {len(results)} products")
                        return results
                    
                    print(f"DEBUG: About to remove lowest confidence filter")
                    # Remove lowest confidence filter
                    removed = active_filters.pop(0)
                    print(f"DEBUG: Removed filter: {removed.name}")
                    
                    relaxation_step = f"{removed.name} (confidence: {removed.confidence:.2f})"
                    relaxation_steps.append(relaxation_step)
                    
                    # Log relaxation step
                    if self.log_callback and self.session_id:
                        try:
                            self.log_callback(self.session_id, "recommendation_stage1", {
                                "relaxed_filter": removed.name,
                                "filter_confidence": removed.confidence,
                                "remaining_filters": len(active_filters)
                            })
                        except Exception as e:
                            print(f"ERROR: Logging callback failed: {e}")
                    
                    print(f"Relaxing filter: {relaxation_step}")
                    
                except Exception as e:
                    print(f"ERROR: Error in progressive filtering loop: {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
                    print(f"ERROR: active_filters count: {len(active_filters)}")
                    print(f"ERROR: active_filters: {[f.name for f in active_filters]}")
                    return []
            
        except Exception as e:
            print(f"ERROR: Fatal error in apply_progressive_filtering: {e}")
            print(f"ERROR: Full traceback:")
            print(traceback.format_exc())
            print(f"ERROR: filters count: {len(filters)}")
            print(f"ERROR: filters: {[f.name for f in filters]}")
            return []
        
        # Fallback (should never reach here)
        print("Fallback: returning first products from catalog")
        return self.catalog.products[:self.target_count]
    
    def apply_filters(self, active_filters: List[Union[AttributeFilter, PriceFilter]]) -> List[Product]:
        """Apply all active filters to the product catalog"""
        results = self.catalog.products.copy()
        
        for filter_obj in active_filters:
            if isinstance(filter_obj, AttributeFilter):
                results = self.apply_attribute_filter(results, filter_obj)
            elif isinstance(filter_obj, PriceFilter):
                results = self.apply_price_filter(results, filter_obj)
        
        return results
    
    def apply_attribute_filter(self, products: List[Product], filter_obj: AttributeFilter) -> List[Product]:
        """Apply OR logic within attribute values"""
        matching = []
        
        print(f"DEBUG: Applying filter '{filter_obj.name}' with values {filter_obj.values}")
        print(f"DEBUG: Processing {len(products)} products")
        
        try:
            for i, product in enumerate(products):
                try:
                    print(f"DEBUG: Processing product {i}: {product.name}")
                    
                    # Special handling for sizes attribute
                    if filter_obj.name == 'sizes':
                        print(f"DEBUG: Sizes filter - product.available_sizes: {product.available_sizes} (type: {type(product.available_sizes)})")
                        
                        # Check if any of the user's desired sizes are available in the product
                        # Ensure product.available_sizes is a list
                        available_sizes = product.available_sizes if isinstance(product.available_sizes, list) else []
                        print(f"DEBUG: Converted available_sizes: {available_sizes}")
                        
                        if any(size in available_sizes for size in filter_obj.values):
                            print(f"DEBUG: Product {product.name} matches size filter")
                            matching.append(product)
                        else:
                            print(f"DEBUG: Product {product.name} does not match size filter")
                    else:
                        product_value = getattr(product, filter_obj.name, None)
                        print(f"DEBUG: Product {product.name} - {filter_obj.name}: {product_value}")
                        
                        # OR logic: product matches if its value is in any of the filter values
                        if product_value and product_value in filter_obj.values:
                            print(f"DEBUG: Product {product.name} matches {filter_obj.name} filter")
                            matching.append(product)
                        else:
                            print(f"DEBUG: Product {product.name} does not match {filter_obj.name} filter")
                            
                except Exception as e:
                    print(f"ERROR: Processing product {i} ({product.name}): {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
                    print(f"ERROR: Product data: {vars(product)}")
                    
        except Exception as e:
            print(f"ERROR: Fatal error in apply_attribute_filter for {filter_obj.name}: {e}")
            print(f"ERROR: Full traceback:")
            print(traceback.format_exc())
            print(f"ERROR: Filter values: {filter_obj.values}")
            print(f"ERROR: Products count: {len(products)}")
            
            # Log the error if callback is available
            if self.log_callback and self.session_id:
                self.log_callback(self.session_id, "error", {
                    "message": f"Filter application failed for {filter_obj.name}: {str(e)}",
                    "filter_values": filter_obj.values,
                    "products_count": len(products),
                    "traceback": traceback.format_exc()
                })
            return []
        
        print(f"DEBUG: Filter '{filter_obj.name}' matched {len(matching)} products")
        return matching
    
    def apply_price_filter(self, products: List[Product], filter_obj: PriceFilter) -> List[Product]:
        """Apply price range filter"""
        matching = []
        
        for product in products:
            if filter_obj.min_price and product.price < filter_obj.min_price:
                continue
            if filter_obj.max_price and product.price > filter_obj.max_price:
                continue
            matching.append(product)
        
        return matching
