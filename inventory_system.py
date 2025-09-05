import time
import threading
from typing import Any, Dict, List, Optional

try:
    from shared_data_manager import shared_data
    SHARED = True
except Exception:
    SHARED = False


class InventoryProvider:
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        return []

    def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        return None

    def get_departments(self) -> List[Dict[str, Any]]:
        return []


def _normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sku": raw.get("sku") or raw.get("id") or "",
        "name": raw.get("name") or raw.get("title") or "",
        "price_cents": int(round(float(raw.get("price", raw.get("price_cents", 0))) * 100)) if not isinstance(raw.get("price", 0), int) else raw.get("price", 0),
        "stock_qty": raw.get("stock_quantity", raw.get("quantity", 0)),
        "aisle": raw.get("aisle") or raw.get("location"),
        "department": raw.get("department") or raw.get("dept"),
        "upc": raw.get("upc"),
        "last_updated": raw.get("updated_at"),
    }


class JSONProvider(InventoryProvider):
    def __init__(self):
        self._has_shared = SHARED

    def search_items(self, query: str) -> List[Dict[str, Any]]:
        if not self._has_shared:
            return []
        items = shared_data.get_inventory() or []
        q = (query or "").lower()
        out = []
        for it in items:
            name = (it.get("name") or "").lower()
            sku = (it.get("sku") or "").lower()
            if q in name or q in sku:
                out.append(_normalize_item(it))
        return out

    def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        if not self._has_shared:
            return None
        for it in shared_data.get_inventory() or []:
            if (it.get("sku") or "").lower() == (sku or "").lower():
                return _normalize_item(it)
        return None

    def get_departments(self) -> List[Dict[str, Any]]:
        if not self._has_shared:
            return []
        return list(shared_data.get_departments() or [])


class ProviderRegistry:
    _lock = threading.Lock()
    _cached_provider: Optional[InventoryProvider] = None
    _cached_key: Optional[str] = None

    @classmethod
    def get_provider(cls) -> InventoryProvider:
        provider_key = "json"
        if SHARED:
            try:
                s = shared_data.get_settings() or {}
                inv = (s.get("integrations") or {}).get("inventory") or {}
                provider_key = (inv.get("provider") or "json").lower()
            except Exception:
                provider_key = "json"

        with cls._lock:
            if cls._cached_provider and cls._cached_key == provider_key:
                return cls._cached_provider

            # Only JSONProvider for now; future: WalmartProvider/KrogerProvider/TargetProvider
            prov: InventoryProvider = JSONProvider()
            cls._cached_provider = prov
            cls._cached_key = provider_key
            return prov


def _with_timeout(callable_fn, *args, timeout_sec: float = 3.0, fallback=None, **kwargs):
    start = time.time()
    try:
        result = callable_fn(*args, **kwargs)
        return result
    except Exception as e:
        print(f"[INVENTORY] provider error: {e}")
        return fallback
    finally:
        dur = (time.time() - start) * 1000
        print(f"[INVENTORY] call {callable_fn.__name__} took {dur:.0f}ms")


def search_inventory(search_term: str) -> List[Dict[str, Any]]:
    prov = ProviderRegistry.get_provider()
    return _with_timeout(prov.search_items, search_term, timeout_sec=3.0, fallback=[])


def get_item_by_sku(sku: str) -> Optional[Dict[str, Any]]:
    prov = ProviderRegistry.get_provider()
    return _with_timeout(prov.get_item_by_sku, sku, timeout_sec=3.0, fallback=None)


def get_price(sku: str) -> Optional[float]:
    item = get_item_by_sku(sku)
    if not item:
        return None
    cents = item.get("price_cents") or 0
    try:
        return round(cents / 100.0, 2)
    except Exception:
        return None


def generate_simulated_inventory_response(search_term: str):
    # Simple demo fallback: fake some numbers for grocery-like items
    name = search_term.strip().title()
    dept = "Grocery"
    price = 3.99
    qty = 12
    return name, dept, price, qty

"""
Inventory Management System for AI Call Router
Supports both simulated data and real inventory system integration
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random

@dataclass
class InventoryItem:
    """Represents a single inventory item"""
    sku: str
    name: str
    department: str
    aisle: str
    shelf: str
    price: float
    quantity: int
    min_quantity: int = 0
    max_quantity: int = 100
    unit: str = "each"
    brand: str = ""
    description: str = ""
    last_updated: str = ""
    is_active: bool = True

@dataclass
class InventorySearchResult:
    """Result of an inventory search"""
    found: bool
    items: List[InventoryItem]
    total_count: int
    search_term: str
    suggestions: List[str] = None

class InventoryManager:
    """Manages inventory data and operations"""
    
    def __init__(self, data_source: str = "simulated"):
        self.data_source = data_source
        self.inventory: Dict[str, InventoryItem] = {}
        self.department_aisles: Dict[str, List[str]] = {}
        self.search_index: Dict[str, List[str]] = {}
        
        # Initialize based on data source
        if data_source == "simulated":
            self._load_simulated_data()
        elif data_source == "json":
            self._load_json_data()
        elif data_source == "database":
            self._load_database_data()
    
    def _load_simulated_data(self):
        """Load simulated inventory data"""
        self.inventory = self._generate_simulated_inventory()
        self._build_search_index()
        self._build_department_aisles()
    
    def _generate_simulated_inventory(self) -> Dict[str, InventoryItem]:
        """Generate realistic simulated inventory data"""
        inventory = {}
        
        # Grocery items
        grocery_items = [
            ("GROC001", "Juanita's Tortilla Chips", "Grocery", "A1", "S1", 3.99, 45),
            ("GROC002", "Doritos Nacho Cheese", "Grocery", "A1", "S1", 4.49, 23),
            ("GROC003", "Lay's Classic Potato Chips", "Grocery", "A1", "S1", 3.99, 67),
            ("GROC004", "Lindor Truffles", "Grocery", "A2", "S3", 8.99, 12),
            ("GROC005", "Hershey's Chocolate Bar", "Grocery", "A2", "S3", 1.99, 89),
            ("GROC006", "Snickers Candy Bar", "Grocery", "A2", "S3", 1.49, 156),
            ("GROC007", "Coca-Cola 12-pack", "Grocery", "A3", "S2", 5.99, 34),
            ("GROC008", "Pepsi 12-pack", "Grocery", "A3", "S2", 5.99, 28),
            ("GROC009", "Dasani Water 24-pack", "Grocery", "A3", "S1", 4.99, 78),
            ("GROC010", "Wonder Bread", "Grocery", "A4", "S1", 2.99, 23),
        ]
        
        # Dairy items
        dairy_items = [
            ("DAIRY001", "Gallon Whole Milk", "Dairy", "B1", "S1", 3.49, 45),
            ("DAIRY002", "Cheddar Cheese Block", "Dairy", "B1", "S2", 4.99, 23),
            ("DAIRY003", "Greek Yogurt", "Dairy", "B1", "S3", 5.99, 34),
            ("DAIRY004", "Butter Unsalted", "Dairy", "B1", "S4", 3.99, 56),
            ("DAIRY005", "Large Eggs 12-pack", "Dairy", "B1", "S5", 4.49, 67),
        ]
        
        # Produce items
        produce_items = [
            ("PROD001", "Organic Bananas", "Produce", "C1", "S1", 1.99, 89),
            ("PROD002", "Red Apples", "Produce", "C1", "S2", 2.99, 45),
            ("PROD003", "Fresh Tomatoes", "Produce", "C2", "S1", 3.99, 34),
            ("PROD004", "Iceberg Lettuce", "Produce", "C2", "S2", 1.49, 67),
            ("PROD005", "Organic Carrots", "Produce", "C3", "S1", 2.49, 78),
        ]
        
        # Household items
        household_items = [
            ("HH001", "Tide Pods Spring Meadow", "Household", "D1", "S1", 12.99, 23),
            ("HH002", "Dawn Ultra Dish Soap", "Household", "D1", "S2", 3.99, 45),
            ("HH003", "Method Foaming Hand Soap", "Household", "D1", "S3", 4.99, 34),
            ("HH004", "Bounty Paper Towels", "Household", "D2", "S1", 8.99, 56),
            ("HH005", "Charmin Toilet Paper", "Household", "D2", "S2", 9.99, 67),
        ]
        
        # Health & Beauty items
        beauty_items = [
            ("BEAUTY001", "Dove Body Wash", "Health & Beauty", "E1", "S1", 5.99, 34),
            ("BEAUTY002", "Head & Shoulders Shampoo", "Health & Beauty", "E1", "S2", 6.99, 45),
            ("BEAUTY003", "Colgate Toothpaste", "Health & Beauty", "E2", "S1", 3.99, 78),
            ("BEAUTY004", "Dove Deodorant", "Health & Beauty", "E2", "S2", 4.99, 56),
            ("BEAUTY005", "CoverGirl Foundation", "Health & Beauty", "E3", "S1", 12.99, 23),
        ]
        
        # Pharmacy items
        pharmacy_items = [
            ("PHARM001", "Airborne Chewables", "Pharmacy", "F1", "S1", 8.99, 34),
            ("PHARM002", "Benadryl Allergy", "Pharmacy", "F1", "S2", 6.99, 45),
            ("PHARM003", "Tylenol Extra Strength", "Pharmacy", "F1", "S3", 7.99, 67),
            ("PHARM004", "Emergen-C Vitamin C", "Pharmacy", "F2", "S1", 9.99, 23),
            ("PHARM005", "Zicam Cold Remedy", "Pharmacy", "F2", "S2", 8.99, 34),
        ]
        
        # Hardware items
        hardware_items = [
            ("HW001", "Great Stuff Gaps and Cracks", "Hardware", "G1", "S1", 4.99, 23),
            ("HW002", "Duct Tape", "Hardware", "G1", "S2", 3.99, 45),
            ("HW003", "WD-40", "Hardware", "G1", "S3", 5.99, 34),
            ("HW004", "Phillips Screwdriver", "Hardware", "G2", "S1", 8.99, 12),
            ("HW005", "Hammer", "Hardware", "G2", "S2", 12.99, 8),
        ]
        
        # Combine all items
        all_items = (grocery_items + dairy_items + produce_items + 
                    household_items + beauty_items + pharmacy_items + hardware_items)
        
        # Create InventoryItem objects
        for sku, name, dept, aisle, shelf, price, qty in all_items:
            inventory[sku] = InventoryItem(
                sku=sku,
                name=name,
                department=dept,
                aisle=aisle,
                shelf=shelf,
                price=price,
                quantity=qty,
                last_updated=datetime.now().isoformat()
            )
        
        return inventory
    
    def _build_search_index(self):
        """Build search index for fast lookups"""
        self.search_index = {}
        
        for sku, item in self.inventory.items():
            # Index by name words
            words = item.name.lower().split()
            for word in words:
                if word not in self.search_index:
                    self.search_index[word] = []
                self.search_index[word].append(sku)
            
            # Index by brand
            if item.brand:
                brand_words = item.brand.lower().split()
                for word in brand_words:
                    if word not in self.search_index:
                        self.search_index[word] = []
                    self.search_index[word].append(sku)
    
    def _build_department_aisles(self):
        """Build department to aisle mapping"""
        self.department_aisles = {}
        
        for item in self.inventory.values():
            if item.department not in self.department_aisles:
                self.department_aisles[item.department] = []
            if item.aisle not in self.department_aisles[item.department]:
                self.department_aisles[item.department].append(item.aisle)
    
    def search_inventory(self, search_term: str) -> InventorySearchResult:
        """Search inventory by name, brand, or description"""
        search_term = search_term.lower().strip()
        found_skus = set()
        
        # Direct SKU search
        if search_term in self.inventory:
            found_skus.add(search_term)
        
        # Word-based search
        search_words = search_term.split()
        for word in search_words:
            if word in self.search_index:
                found_skus.update(self.search_index[word])
        
        # Fuzzy search for partial matches
        for sku, item in self.inventory.items():
            if search_term in item.name.lower():
                found_skus.add(sku)
            elif item.brand and search_term in item.brand.lower():
                found_skus.add(sku)
        
        # Get items
        items = [self.inventory[sku] for sku in found_skus if sku in self.inventory]
        
        # Generate suggestions if no exact match
        suggestions = []
        if not items:
            suggestions = self._generate_search_suggestions(search_term)
        
        return InventorySearchResult(
            found=len(items) > 0,
            items=items,
            total_count=len(items),
            search_term=search_term,
            suggestions=suggestions
        )
    
    def generate_simulated_response(self, search_term: str, query_type: str = "general") -> tuple[str, str, float, int]:
        """
        Generate realistic simulated responses for any grocery item
        Returns: (item_name, department, price, quantity)
        """
        import random
        
        # Clean up search term
        clean_term = search_term.lower().strip()
        
        # Remove common query words and phrases
        query_words = [
            "price", "check", "cost", "how much", "stock", "available", "have", "carry",
            "do you", "what's", "what is", "the price of", "price of", "price for",
            "how much does", "how much is", "price check on", "cost of", "cost for"
        ]
        
        for word in query_words:
            clean_term = clean_term.replace(word, "").strip()
        
        # Clean up extra spaces and punctuation
        clean_term = " ".join(clean_term.split())
        clean_term = clean_term.strip(".,!?")
        
        # Extract the actual item name more intelligently
        # Look for common patterns and extract the item
        words = clean_term.split()
        
        # Remove common filler words
        filler_words = ["the", "a", "an", "of", "for", "on", "in", "at", "to", "with", "by"]
        words = [word for word in words if word.lower() not in filler_words]
        
        # Reconstruct the item name
        if words:
            clean_term = " ".join(words)
        else:
            # Fallback to original term if no words left
            clean_term = search_term.lower().strip()
        
        # Determine item category and generate realistic data
        if any(word in clean_term for word in ["bread", "dave", "killer"]):
            # Bread category
            bread_variants = [
                ("Dave's Killer Bread", "Grocery", 4.99, random.randint(15, 45)),
                ("Dave's Killer Bread 21 Whole Grains", "Grocery", 5.49, random.randint(10, 35)),
                ("Dave's Killer Bread Good Seed", "Grocery", 5.99, random.randint(8, 25)),
                ("Dave's Killer Bread Powerseed", "Grocery", 5.79, random.randint(12, 30))
            ]
            return random.choice(bread_variants)
        
        elif any(word in clean_term for word in ["milk", "dairy"]):
            # Dairy category
            if "organic" in clean_term:
                dairy_variants = [
                    ("Organic Whole Milk", "Dairy", 4.49, random.randint(20, 50)),
                    ("Organic 2% Milk", "Dairy", 4.29, random.randint(15, 40)),
                    ("Organic Almond Milk", "Dairy", 3.49, random.randint(15, 40))
                ]
            else:
                dairy_variants = [
                    ("Organic Whole Milk", "Dairy", 4.49, random.randint(20, 50)),
                    ("2% Reduced Fat Milk", "Dairy", 3.99, random.randint(25, 60)),
                    ("Almond Milk", "Dairy", 3.49, random.randint(15, 40)),
                    ("Oat Milk", "Dairy", 4.99, random.randint(10, 30))
                ]
            return random.choice(dairy_variants)
        
        elif any(word in clean_term for word in ["chips", "snack"]):
            # Snack category
            if "doritos" in clean_term:
                snack_variants = [
                    ("Doritos Nacho Cheese", "Grocery", 4.49, random.randint(15, 40)),
                    ("Doritos Cool Ranch", "Grocery", 4.49, random.randint(12, 35)),
                    ("Doritos Spicy Nacho", "Grocery", 4.49, random.randint(10, 30))
                ]
            elif "lays" in clean_term or "lay's" in clean_term:
                snack_variants = [
                    ("Lay's Classic Potato Chips", "Grocery", 3.99, random.randint(20, 50)),
                    ("Lay's Sour Cream & Onion", "Grocery", 3.99, random.randint(18, 45)),
                    ("Lay's Barbecue", "Grocery", 3.99, random.randint(15, 40))
                ]
            else:
                snack_variants = [
                    ("Lay's Classic Potato Chips", "Grocery", 3.99, random.randint(20, 50)),
                    ("Doritos Nacho Cheese", "Grocery", 4.49, random.randint(15, 40)),
                    ("Pringles Original", "Grocery", 3.79, random.randint(25, 55)),
                    ("Cheetos Crunchy", "Grocery", 3.99, random.randint(18, 45))
                ]
            return random.choice(snack_variants)
        
        elif any(word in clean_term for word in ["cereal", "breakfast", "cheerios"]):
            # Cereal category
            if "honey nut" in clean_term or "honey nut cheerios" in clean_term:
                cereal_variants = [
                    ("Honey Nut Cheerios", "Grocery", 5.49, random.randint(12, 30)),
                    ("Honey Nut Cheerios Family Size", "Grocery", 6.99, random.randint(8, 20))
                ]
            elif "cheerios" in clean_term:
                cereal_variants = [
                    ("Cheerios Original", "Grocery", 4.99, random.randint(15, 35)),
                    ("Honey Nut Cheerios", "Grocery", 5.49, random.randint(12, 30))
                ]
            else:
                cereal_variants = [
                    ("Cheerios Original", "Grocery", 4.99, random.randint(15, 35)),
                    ("Frosted Flakes", "Grocery", 3.99, random.randint(20, 45)),
                    ("Raisin Bran", "Grocery", 4.49, random.randint(10, 25)),
                    ("Honey Nut Cheerios", "Grocery", 5.49, random.randint(12, 30))
                ]
            return random.choice(cereal_variants)
        
        elif any(word in clean_term for word in ["soda", "pop", "cola", "drink"]):
            # Beverage category
            if "coca" in clean_term or "coke" in clean_term:
                beverage_variants = [
                    ("Coca-Cola 12-pack", "Grocery", 5.99, random.randint(30, 70)),
                    ("Coca-Cola 24-pack", "Grocery", 10.99, random.randint(15, 40)),
                    ("Diet Coke 12-pack", "Grocery", 5.99, random.randint(15, 40))
                ]
            elif "pepsi" in clean_term:
                beverage_variants = [
                    ("Pepsi 12-pack", "Grocery", 5.99, random.randint(25, 60)),
                    ("Pepsi 24-pack", "Grocery", 10.99, random.randint(12, 35))
                ]
            else:
                beverage_variants = [
                    ("Coca-Cola 12-pack", "Grocery", 5.99, random.randint(30, 70)),
                    ("Pepsi 12-pack", "Grocery", 5.99, random.randint(25, 60)),
                    ("Sprite 12-pack", "Grocery", 5.49, random.randint(20, 50)),
                    ("Diet Coke 12-pack", "Grocery", 5.99, random.randint(15, 40))
                ]
            return random.choice(beverage_variants)
        
        elif any(word in clean_term for word in ["fruit", "apple", "banana", "orange"]):
            # Produce category
            if "banana" in clean_term:
                if "organic" in clean_term:
                    produce_variants = [
                        ("Organic Bananas", "Produce", 1.99, random.randint(50, 100)),
                        ("Organic Bananas Bunch", "Produce", 2.49, random.randint(30, 80))
                    ]
                else:
                    produce_variants = [
                        ("Organic Bananas", "Produce", 1.99, random.randint(50, 100)),
                        ("Bananas Bunch", "Produce", 1.49, random.randint(60, 120))
                    ]
            elif "apple" in clean_term:
                produce_variants = [
                    ("Red Delicious Apples", "Produce", 2.99, random.randint(30, 80)),
                    ("Gala Apples", "Produce", 3.49, random.randint(25, 70)),
                    ("Granny Smith Apples", "Produce", 2.79, random.randint(20, 60))
                ]
            else:
                produce_variants = [
                    ("Organic Bananas", "Produce", 1.99, random.randint(50, 100)),
                    ("Red Delicious Apples", "Produce", 2.99, random.randint(30, 80)),
                    ("Navel Oranges", "Produce", 3.99, random.randint(25, 60)),
                    ("Strawberries", "Produce", 4.99, random.randint(15, 40))
                ]
            return random.choice(produce_variants)
        
        elif any(word in clean_term for word in ["meat", "chicken", "beef", "pork"]):
            # Meat category
            meat_variants = [
                ("Ground Beef 80/20", "Meat & Seafood", 8.99, random.randint(10, 30)),
                ("Chicken Breast", "Meat & Seafood", 6.99, random.randint(15, 40)),
                ("Pork Chops", "Meat & Seafood", 7.99, random.randint(8, 25)),
                ("Salmon Fillet", "Meat & Seafood", 12.99, random.randint(5, 20))
            ]
            return random.choice(meat_variants)
        
        elif any(word in clean_term for word in ["yogurt", "cheese", "butter"]):
            # Dairy products
            dairy_product_variants = [
                ("Greek Yogurt", "Dairy", 5.99, random.randint(20, 50)),
                ("Cheddar Cheese Block", "Dairy", 4.99, random.randint(15, 35)),
                ("Butter Unsalted", "Dairy", 3.99, random.randint(25, 60)),
                ("Cream Cheese", "Dairy", 2.99, random.randint(20, 45))
            ]
            return random.choice(dairy_product_variants)
        
        else:
            # Generic grocery item - generate based on search term
            # Extract key words for categorization
            words = clean_term.split()
            
            # Determine department and price range based on words
            if any(word in words for word in ["organic", "natural", "healthy"]):
                department = "Produce"
                base_price = random.uniform(3.99, 7.99)
            elif any(word in words for word in ["premium", "gourmet", "artisan"]):
                department = "Grocery"
                base_price = random.uniform(5.99, 12.99)
            elif any(word in words for word in ["budget", "value", "store"]):
                department = "Grocery"
                base_price = random.uniform(1.99, 4.99)
            else:
                department = "Grocery"
                base_price = random.uniform(2.99, 6.99)
            
            # Generate item name
            if len(words) >= 2:
                item_name = f"{words[0].title()} {words[1].title()}"
            else:
                item_name = clean_term.title()
            
            # Add some variety to the name
            if random.random() < 0.3:
                item_name += " Premium"
            elif random.random() < 0.2:
                item_name += " Organic"
            
            quantity = random.randint(10, 50)
            price = round(base_price, 2)
            
            return (item_name, department, price, quantity)
    
    def _generate_search_suggestions(self, search_term: str) -> List[str]:
        """Generate search suggestions for failed searches"""
        suggestions = []
        
        # Find similar words
        for word in self.search_index.keys():
            if search_term in word or word in search_term:
                # Get a sample item for this word
                if self.search_index[word]:
                    sample_sku = self.search_index[word][0]
                    if sample_sku in self.inventory:
                        suggestions.append(self.inventory[sample_sku].name)
                        if len(suggestions) >= 3:
                            break
        
        return suggestions
    
    def get_item_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """Get item by SKU"""
        return self.inventory.get(sku)
    
    def get_items_by_department(self, department: str) -> List[InventoryItem]:
        """Get all items in a department"""
        return [item for item in self.inventory.values() if item.department == department]
    
    def get_aisle_location(self, department: str) -> List[str]:
        """Get aisle locations for a department"""
        return self.department_aisles.get(department, [])
    
    def check_stock(self, sku: str) -> Tuple[bool, int]:
        """Check if item is in stock and return quantity"""
        item = self.inventory.get(sku)
        if not item:
            return False, 0
        return item.quantity > 0, item.quantity
    
    def get_price(self, sku: str) -> Optional[float]:
        """Get price for an item"""
        item = self.inventory.get(sku)
        return item.price if item else None
    
    def update_quantity(self, sku: str, new_quantity: int) -> bool:
        """Update item quantity (for real inventory integration)"""
        if sku not in self.inventory:
            return False
        
        self.inventory[sku].quantity = max(0, new_quantity)
        self.inventory[sku].last_updated = datetime.now().isoformat()
        return True
    
    def get_low_stock_items(self, threshold: int = 10) -> List[InventoryItem]:
        """Get items with low stock"""
        return [item for item in self.inventory.values() if item.quantity <= threshold]
    
    def get_department_summary(self, department: str) -> Dict[str, Any]:
        """Get summary statistics for a department"""
        items = self.get_items_by_department(department)
        if not items:
            return {}
        
        total_items = len(items)
        total_value = sum(item.price * item.quantity for item in items)
        low_stock = len([item for item in items if item.quantity <= 10])
        out_of_stock = len([item for item in items if item.quantity == 0])
        
        return {
            "department": department,
            "total_items": total_items,
            "total_value": round(total_value, 2),
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock,
            "aisles": self.get_aisle_location(department)
        }
    
    def export_to_json(self, filename: str = "inventory_export.json"):
        """Export inventory to JSON file"""
        data = {
            "export_date": datetime.now().isoformat(),
            "data_source": self.data_source,
            "items": [asdict(item) for item in self.inventory.values()]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filename: str):
        """Import inventory from JSON file"""
        if not os.path.exists(filename):
            return False
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.inventory.clear()
        for item_data in data.get("items", []):
            item = InventoryItem(**item_data)
            self.inventory[item.sku] = item
        
        self._build_search_index()
        self._build_department_aisles()
        return True

# Global inventory manager instance
inventory_manager = InventoryManager()

# Convenience functions for easy access
def search_inventory(search_term: str) -> InventorySearchResult:
    """Search inventory by term"""
    return inventory_manager.search_inventory(search_term)

def get_item_by_sku(sku: str) -> Optional[InventoryItem]:
    """Get item by SKU"""
    return inventory_manager.get_item_by_sku(sku)

def check_stock(sku: str) -> Tuple[bool, int]:
    """Check stock for item"""
    return inventory_manager.check_stock(sku)

def get_price(sku: str) -> Optional[float]:
    """Get price for item"""
    return inventory_manager.get_price(sku)

def get_department_summary(department: str) -> Dict[str, Any]:
    """Get department summary"""
    return inventory_manager.get_department_summary(department)

def generate_simulated_inventory_response(search_term: str) -> tuple[str, str, float, int]:
    """Generate realistic simulated response for any grocery item"""
    return inventory_manager.generate_simulated_response(search_term)
