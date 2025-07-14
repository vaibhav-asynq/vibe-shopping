"""
Product catalog management - loads products from Excel file
"""
import pandas as pd
import traceback
from typing import List
from .models import Product


class ProductCatalog:
    """Manages product catalog loaded from Excel file"""
    
    def __init__(self, excel_path: str = "Apparels_shared.xlsx"):
        self.products = self.load_products_from_excel(excel_path)
        print(f"Loaded {len(self.products)} products from catalog")
    
    def load_products_from_excel(self, path: str) -> List[Product]:
        """Load products from Excel file and convert to Product objects"""
        try:
            # Read Excel file
            df = pd.read_excel(path)
            products = []
            
            for i, row in df.iterrows():
                try:
                    print(f"DEBUG: Loading product {i}: {row.get('name', 'unknown')}")
                    
                    # Parse sizes from comma-separated string with robust error handling
                    try:
                        raw_sizes = row['available_sizes']
                        print(f"DEBUG: Raw available_sizes: {raw_sizes} (type: {type(raw_sizes)})")
                        
                        sizes_str = str(raw_sizes) if pd.notna(raw_sizes) else ""
                        print(f"DEBUG: Converted to string: '{sizes_str}'")
                        
                        if sizes_str and sizes_str != 'nan':
                            available_sizes = [size.strip() for size in sizes_str.split(',') if size.strip()]
                        else:
                            available_sizes = []
                        
                        print(f"DEBUG: Final available_sizes: {available_sizes} (type: {type(available_sizes)})")
                        
                    except Exception as e:
                        print(f"ERROR: Parsing sizes for product {row.get('name', 'unknown')}: {e}")
                        print(f"ERROR: Full traceback:")
                        print(traceback.format_exc())
                        available_sizes = []
                    
                    # Create Product object
                    product = Product(
                        id=str(row['id']),
                        name=str(row['name']),
                        category=str(row['category']),
                        available_sizes=available_sizes,
                        fit=str(row['fit']) if pd.notna(row['fit']) else None,
                        fabric=str(row['fabric']) if pd.notna(row['fabric']) else None,
                        sleeve_length=str(row['sleeve_length']) if pd.notna(row['sleeve_length']) else None,
                        color_or_print=str(row['color_or_print']) if pd.notna(row['color_or_print']) else None,
                        occasion=str(row['occasion']) if pd.notna(row['occasion']) else None,
                        neckline=str(row['neckline']) if pd.notna(row['neckline']) else None,
                        length=str(row['length']) if pd.notna(row['length']) else None,
                        pant_type=str(row['pant_type']) if pd.notna(row['pant_type']) else None,
                        price=float(row['price'])
                    )
                    
                    # Validate the created product
                    print(f"DEBUG: Created product with available_sizes: {product.available_sizes} (type: {type(product.available_sizes)})")
                    
                    products.append(product)
                    
                except Exception as e:
                    print(f"ERROR: Failed to create product {i}: {e}")
                    print(f"ERROR: Full traceback:")
                    print(traceback.format_exc())
                    print(f"ERROR: Row data: {dict(row)}")
            
            return products
            
        except Exception as e:
            print(f"Error loading products from {path}: {e}")
            return []
    
    def get_products_by_category(self, category: str) -> List[Product]:
        """Get all products in a specific category"""
        return [p for p in self.products if p.category.lower() == category.lower()]
    
    def get_products_in_price_range(self, min_price: float = None, max_price: float = None) -> List[Product]:
        """Get products within a price range"""
        return [p for p in self.products if p.matches_price_range(min_price, max_price)]
    
    def get_products_by_size(self, size: str) -> List[Product]:
        """Get products available in a specific size"""
        return [p for p in self.products if p.matches_size(size)]
