"""
Coupon System for Grocery Store
Handles coupon lookups, discount codes, and promotional offers
"""

import re
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

@dataclass
class Coupon:
    """Represents a coupon or discount offer"""
    id: str
    name: str
    description: str
    discount_type: str  # "percentage", "dollar_off", "buy_one_get_one", "free_item"
    discount_value: float
    minimum_purchase: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    applicable_items: List[str] = None
    applicable_categories: List[str] = None
    code: Optional[str] = None
    restrictions: List[str] = None

@dataclass
class CouponQuery:
    """Represents a coupon lookup request"""
    item: Optional[str] = None
    category: Optional[str] = None
    customer_id: Optional[str] = None
    query_type: str = "general"  # "item_specific", "category", "general", "code_lookup"

class CouponManager:
    """Manages coupon lookups and discount information"""
    
    def __init__(self):
        self.coupons = []
        self._load_simulated_coupons()
    
    def _load_simulated_coupons(self):
        """Load simulated coupon data for demonstration"""
        today = datetime.now()
        
        # General store coupons
        self.coupons.extend([
            Coupon(
                id="STORE001",
                name="10% Off Your Entire Purchase",
                description="Save 10% on your entire grocery purchase",
                discount_type="percentage",
                discount_value=10.0,
                minimum_purchase=50.0,
                valid_until=today + timedelta(days=7),
                code="SAVE10",
                restrictions=["Cannot be combined with other offers", "Excludes alcohol and tobacco"]
            ),
            Coupon(
                id="STORE002", 
                name="$5 Off $50 Purchase",
                description="Save $5 when you spend $50 or more",
                discount_type="dollar_off",
                discount_value=5.0,
                minimum_purchase=50.0,
                valid_until=today + timedelta(days=14),
                code="SAVE5",
                restrictions=["Cannot be combined with other offers"]
            ),
            Coupon(
                id="STORE003",
                name="Buy One Get One 50% Off",
                description="Buy one item, get the second at 50% off",
                discount_type="buy_one_get_one",
                discount_value=50.0,
                valid_until=today + timedelta(days=30),
                restrictions=["Valid on select items only", "Cannot be combined with other offers"]
            )
        ])
        
        # Dairy coupons
        self.coupons.extend([
            Coupon(
                id="DAIRY001",
                name="20% Off All Milk Products",
                description="Save 20% on milk, cheese, yogurt, and other dairy items",
                discount_type="percentage", 
                discount_value=20.0,
                applicable_categories=["dairy", "milk", "cheese", "yogurt"],
                valid_until=today + timedelta(days=5),
                code="DAIRY20",
                restrictions=["Valid on dairy products only"]
            ),
            Coupon(
                id="DAIRY002",
                name="$2 Off Any Cheese Purchase",
                description="Save $2 on any cheese product",
                discount_type="dollar_off",
                discount_value=2.0,
                applicable_categories=["cheese"],
                valid_until=today + timedelta(days=10),
                code="CHEESE2"
            )
        ])
        
        # Cereal coupons
        self.coupons.extend([
            Coupon(
                id="CEREAL001",
                name="Buy 2 Get 1 Free Cereal",
                description="Buy any 2 boxes of cereal, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_categories=["cereal", "breakfast"],
                valid_until=today + timedelta(days=7),
                code="CEREAL3FOR2",
                restrictions=["Valid on cereal products only", "Must buy 2 to get 1 free"]
            ),
            Coupon(
                id="CEREAL002",
                name="15% Off All Cereal",
                description="Save 15% on all cereal products",
                discount_type="percentage",
                discount_value=15.0,
                applicable_categories=["cereal", "breakfast"],
                valid_until=today + timedelta(days=14),
                code="CEREAL15"
            )
        ])
        
        # Produce coupons
        self.coupons.extend([
            Coupon(
                id="PRODUCE001",
                name="$3 Off Fresh Produce",
                description="Save $3 on any fresh produce purchase of $15 or more",
                discount_type="dollar_off",
                discount_value=3.0,
                minimum_purchase=15.0,
                applicable_categories=["produce", "fruits", "vegetables"],
                valid_until=today + timedelta(days=3),
                code="PRODUCE3",
                restrictions=["Minimum $15 purchase required", "Valid on fresh produce only"]
            )
        ])
        
        # Meat coupons
        self.coupons.extend([
            Coupon(
                id="MEAT001",
                name="25% Off All Ground Beef",
                description="Save 25% on all ground beef products",
                discount_type="percentage",
                discount_value=25.0,
                applicable_categories=["meat", "beef", "ground beef"],
                valid_until=today + timedelta(days=5),
                code="BEEF25"
            ),
            Coupon(
                id="MEAT002",
                name="$5 Off Chicken Purchase",
                description="Save $5 on any chicken purchase of $20 or more",
                discount_type="dollar_off",
                discount_value=5.0,
                minimum_purchase=20.0,
                applicable_categories=["meat", "chicken", "poultry"],
                valid_until=today + timedelta(days=7),
                code="CHICKEN5"
            )
        ])
        
        # Pantry/Grocery coupons
        self.coupons.extend([
            Coupon(
                id="PANTRY001",
                name="Buy One Get One Free Pasta",
                description="Buy one box of pasta, get one free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_categories=["pasta", "pantry"],
                valid_until=today + timedelta(days=10),
                code="PASTA2FOR1"
            ),
            Coupon(
                id="PANTRY002",
                name="30% Off All Canned Goods",
                description="Save 30% on all canned vegetables, fruits, and beans",
                discount_type="percentage",
                discount_value=30.0,
                applicable_categories=["canned", "pantry"],
                valid_until=today + timedelta(days=7),
                code="CANNED30"
            )
        ])
        
        # Health & Beauty coupons
        self.coupons.extend([
            Coupon(
                id="BEAUTY001",
                name="$3 Off Personal Care Items",
                description="Save $3 on any personal care purchase of $15 or more",
                discount_type="dollar_off",
                discount_value=3.0,
                minimum_purchase=15.0,
                applicable_categories=["personal care", "beauty", "health", "beauty products"],
                valid_until=today + timedelta(days=14),
                code="BEAUTY3"
            )
        ])
        
        # Household coupons
        self.coupons.extend([
            Coupon(
                id="HOUSEHOLD001",
                name="Buy 2 Get 1 Free Cleaning Products",
                description="Buy 2 cleaning products, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_categories=["cleaning", "household"],
                valid_until=today + timedelta(days=7),
                code="CLEAN3FOR2"
            )
        ])
        
        # Office and Stationery coupons
        self.coupons.extend([
            Coupon(
                id="OFFICE001",
                name="15% Off All Office Supplies",
                description="Save 15% on pens, paper, notebooks, and other office supplies",
                discount_type="percentage",
                discount_value=15.0,
                applicable_categories=["office", "stationery", "office_stationery", "school supplies"],
                valid_until=today + timedelta(days=10),
                code="OFFICE15",
                restrictions=["Valid on office supplies only"]
            ),
            Coupon(
                id="OFFICE002",
                name="$3 Off Sharpie Markers",
                description="Save $3 on any Sharpie marker purchase",
                discount_type="dollar_off",
                discount_value=3.0,
                applicable_items=["sharpie", "sharpie markers", "markers"],
                applicable_categories=["office", "stationery", "office_stationery"],
                valid_until=today + timedelta(days=14),
                code="SHARPIE3"
            ),
            Coupon(
                id="OFFICE003",
                name="Buy 2 Get 1 Free on Pens",
                description="Buy 2 pens, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["pen", "pens", "ballpoint pen", "gel pen"],
                applicable_categories=["office", "stationery", "office_stationery"],
                valid_until=today + timedelta(days=21),
                code="PEN3FOR2"
            )
        ])
        
        # Produce coupons
        self.coupons.extend([
            Coupon(
                id="PRODUCE001",
                name="20% Off All Organic Produce",
                description="Save 20% on all organic fruits and vegetables",
                discount_type="percentage",
                discount_value=20.0,
                applicable_categories=["produce", "organic", "fruits", "vegetables"],
                valid_until=today + timedelta(days=7),
                code="ORGANIC20",
                restrictions=["Valid on organic produce only"]
            ),
            Coupon(
                id="PRODUCE002",
                name="$2 Off Fresh Berries",
                description="Save $2 on any fresh berry purchase",
                discount_type="dollar_off",
                discount_value=2.0,
                applicable_items=["strawberries", "blueberries", "raspberries", "blackberries"],
                applicable_categories=["produce", "fruits", "berries"],
                valid_until=today + timedelta(days=5),
                code="BERRIES2"
            ),
            Coupon(
                id="PRODUCE003",
                name="Buy 3 Get 1 Free on Apples",
                description="Buy 3 apples, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["apple", "apples"],
                applicable_categories=["produce", "fruits"],
                valid_until=today + timedelta(days=10),
                code="APPLE4FOR3"
            )
        ])
        
        # Meat & Seafood coupons
        self.coupons.extend([
            Coupon(
                id="MEAT001",
                name="15% Off All Ground Beef",
                description="Save 15% on ground beef and hamburger meat",
                discount_type="percentage",
                discount_value=15.0,
                applicable_items=["ground beef", "hamburger", "burger meat"],
                applicable_categories=["meat", "beef"],
                valid_until=today + timedelta(days=7),
                code="BEEF15"
            ),
            Coupon(
                id="MEAT002",
                name="$5 Off Chicken Breast",
                description="Save $5 on chicken breast purchase of $20 or more",
                discount_type="dollar_off",
                discount_value=5.0,
                minimum_purchase=20.0,
                applicable_items=["chicken breast", "chicken breasts"],
                applicable_categories=["meat", "chicken", "poultry"],
                valid_until=today + timedelta(days=5),
                code="CHICKEN5"
            ),
            Coupon(
                id="MEAT003",
                name="Buy 2 Get 1 Free on Salmon",
                description="Buy 2 salmon fillets, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["salmon", "salmon fillet", "salmon fillets"],
                applicable_categories=["seafood", "fish"],
                valid_until=today + timedelta(days=3),
                code="SALMON3FOR2"
            )
        ])
        
        # Frozen Food coupons
        self.coupons.extend([
            Coupon(
                id="FROZEN001",
                name="25% Off All Frozen Pizza",
                description="Save 25% on all frozen pizza varieties",
                discount_type="percentage",
                discount_value=25.0,
                applicable_items=["frozen pizza", "pizza"],
                applicable_categories=["frozen", "pizza"],
                valid_until=today + timedelta(days=14),
                code="PIZZA25"
            ),
            Coupon(
                id="FROZEN002",
                name="$3 Off Frozen Vegetables",
                description="Save $3 on frozen vegetable purchase of $10 or more",
                discount_type="dollar_off",
                discount_value=3.0,
                minimum_purchase=10.0,
                applicable_items=["frozen vegetables", "frozen peas", "frozen corn", "frozen broccoli"],
                applicable_categories=["frozen", "vegetables"],
                valid_until=today + timedelta(days=10),
                code="FROZENVEG3"
            ),
            Coupon(
                id="FROZEN003",
                name="Buy 1 Get 1 Free on Ice Cream",
                description="Buy 1 ice cream, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["ice cream", "frozen yogurt", "gelato"],
                applicable_categories=["frozen", "desserts"],
                valid_until=today + timedelta(days=7),
                code="ICECREAM2FOR1"
            )
        ])
        
        # Bakery coupons
        self.coupons.extend([
            Coupon(
                id="BAKERY001",
                name="20% Off All Bread",
                description="Save 20% on all bread varieties",
                discount_type="percentage",
                discount_value=20.0,
                applicable_items=["bread", "sandwich bread", "artisan bread"],
                applicable_categories=["bakery", "bread"],
                valid_until=today + timedelta(days=5),
                code="BREAD20"
            ),
            Coupon(
                id="BAKERY002",
                name="$2 Off Cakes and Pastries",
                description="Save $2 on any cake or pastry purchase",
                discount_type="dollar_off",
                discount_value=2.0,
                applicable_items=["cake", "cakes", "pastry", "pastries", "donut", "donuts"],
                applicable_categories=["bakery", "desserts"],
                valid_until=today + timedelta(days=3),
                code="CAKE2"
            ),
            Coupon(
                id="BAKERY003",
                name="Buy 2 Get 1 Free on Bagels",
                description="Buy 2 bagels, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["bagel", "bagels"],
                applicable_categories=["bakery", "bread"],
                valid_until=today + timedelta(days=7),
                code="BAGEL3FOR2"
            )
        ])
        
        # Pantry/Grocery coupons
        self.coupons.extend([
            Coupon(
                id="PANTRY001",
                name="15% Off All Pasta",
                description="Save 15% on all pasta varieties",
                discount_type="percentage",
                discount_value=15.0,
                applicable_items=["pasta", "spaghetti", "penne", "rigatoni", "fettuccine"],
                applicable_categories=["pantry", "grocery", "pasta"],
                valid_until=today + timedelta(days=14),
                code="PASTA15"
            ),
            Coupon(
                id="PANTRY002",
                name="$1 Off Canned Goods",
                description="Save $1 on any canned food purchase",
                discount_type="dollar_off",
                discount_value=1.0,
                applicable_items=["canned", "can of", "cans of"],
                applicable_categories=["pantry", "grocery", "canned goods"],
                valid_until=today + timedelta(days=21),
                code="CAN1"
            ),
            Coupon(
                id="PANTRY003",
                name="Buy 2 Get 1 Free on Cereal",
                description="Buy 2 cereals, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["cereal", "cereals"],
                applicable_categories=["pantry", "grocery", "breakfast"],
                valid_until=today + timedelta(days=10),
                code="CEREAL3FOR2"
            ),
            Coupon(
                id="PANTRY004",
                name="20% Off All Coffee",
                description="Save 20% on all coffee varieties",
                discount_type="percentage",
                discount_value=20.0,
                applicable_items=["coffee", "ground coffee", "coffee beans", "instant coffee"],
                applicable_categories=["pantry", "grocery", "beverages"],
                valid_until=today + timedelta(days=14),
                code="COFFEE20"
            ),
            Coupon(
                id="PANTRY005",
                name="$3 Off Premium Coffee",
                description="Save $3 on premium coffee purchase of $15 or more",
                discount_type="dollar_off",
                discount_value=3.0,
                minimum_purchase=15.0,
                applicable_items=["premium coffee", "organic coffee", "fair trade coffee"],
                applicable_categories=["pantry", "grocery", "beverages"],
                valid_until=today + timedelta(days=7),
                code="PREMIUMCOFFEE3"
            ),
            Coupon(
                id="PANTRY006",
                name="Buy 2 Get 1 Free on Soda",
                description="Buy 2 sodas, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["soda", "pop", "soft drink", "soft drinks"],
                applicable_categories=["pantry", "grocery", "beverages"],
                valid_until=today + timedelta(days=10),
                code="SODA3FOR2"
            ),
            Coupon(
                id="PANTRY007",
                name="$1 Off Energy Drinks",
                description="Save $1 on any energy drink purchase",
                discount_type="dollar_off",
                discount_value=1.0,
                applicable_items=["energy drink", "energy drinks", "red bull", "monster"],
                applicable_categories=["pantry", "grocery", "beverages"],
                valid_until=today + timedelta(days=14),
                code="ENERGY1"
            )
        ])
        
        # Health & Beauty coupons
        self.coupons.extend([
            Coupon(
                id="BEAUTY001",
                name="20% Off All Shampoo and Conditioner",
                description="Save 20% on all hair care products",
                discount_type="percentage",
                discount_value=20.0,
                applicable_items=["shampoo", "conditioner", "hair care"],
                applicable_categories=["beauty", "personal care", "hair care"],
                valid_until=today + timedelta(days=14),
                code="HAIR20"
            ),
            Coupon(
                id="BEAUTY002",
                name="$3 Off Toothpaste and Toothbrushes",
                description="Save $3 on oral care products",
                discount_type="dollar_off",
                discount_value=3.0,
                applicable_items=["toothpaste", "toothbrush", "toothbrushes"],
                applicable_categories=["beauty", "personal care", "oral care"],
                valid_until=today + timedelta(days=10),
                code="ORAL3"
            ),
            Coupon(
                id="BEAUTY003",
                name="Buy 1 Get 1 Free on Deodorant",
                description="Buy 1 deodorant, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["deodorant", "antiperspirant"],
                applicable_categories=["beauty", "personal care"],
                valid_until=today + timedelta(days=7),
                code="DEODORANT2FOR1"
            )
        ])
        
        # Household/Cleaning coupons
        self.coupons.extend([
            Coupon(
                id="HOUSEHOLD001",
                name="25% Off All Laundry Detergent",
                description="Save 25% on all laundry products",
                discount_type="percentage",
                discount_value=25.0,
                applicable_items=["laundry detergent", "detergent", "fabric softener"],
                applicable_categories=["household", "cleaning", "laundry"],
                valid_until=today + timedelta(days=14),
                code="LAUNDRY25"
            ),
            Coupon(
                id="HOUSEHOLD002",
                name="$2 Off Paper Products",
                description="Save $2 on paper towels, toilet paper, and tissues",
                discount_type="dollar_off",
                discount_value=2.0,
                applicable_items=["paper towels", "toilet paper", "tissues", "napkins"],
                applicable_categories=["household", "paper products"],
                valid_until=today + timedelta(days=10),
                code="PAPER2"
            ),
            Coupon(
                id="HOUSEHOLD003",
                name="Buy 2 Get 1 Free on Cleaning Supplies",
                description="Buy 2 cleaning products, get 1 free",
                discount_type="free_item",
                discount_value=100.0,
                applicable_items=["cleaning", "cleaner", "disinfectant", "bleach"],
                applicable_categories=["household", "cleaning"],
                valid_until=today + timedelta(days=7),
                code="CLEAN3FOR2"
            )
        ])
        
        # Electronics coupons
        self.coupons.extend([
            Coupon(
                id="ELECTRONICS001",
                name="10% Off All Electronics",
                description="Save 10% on all electronics and gadgets",
                discount_type="percentage",
                discount_value=10.0,
                applicable_categories=["electronics", "gadgets", "tech"],
                valid_until=today + timedelta(days=30),
                code="TECH10",
                restrictions=["Valid on electronics only"]
            ),
            Coupon(
                id="ELECTRONICS002",
                name="$5 Off Phone Accessories",
                description="Save $5 on phone cases, chargers, and accessories",
                discount_type="dollar_off",
                discount_value=5.0,
                applicable_items=["phone case", "charger", "cable", "headphones"],
                applicable_categories=["electronics", "phone accessories"],
                valid_until=today + timedelta(days=21),
                code="PHONE5"
            ),
            Coupon(
                id="ELECTRONICS003",
                name="25% Off All Cables",
                description="Save 25% on HDMI, USB, and other cables",
                discount_type="percentage",
                discount_value=25.0,
                applicable_items=["hdmi cable", "hdmi", "usb cable", "usb", "cable", "cables"],
                applicable_categories=["electronics", "cables", "accessories"],
                valid_until=today + timedelta(days=14),
                code="CABLE25"
            ),
            Coupon(
                id="ELECTRONICS004",
                name="$3 Off HDMI Cables",
                description="Save $3 on any HDMI cable purchase",
                discount_type="dollar_off",
                discount_value=3.0,
                applicable_items=["hdmi cable", "hdmi"],
                applicable_categories=["electronics", "cables"],
                valid_until=today + timedelta(days=21),
                code="HDMI3"
            )
        ])
        
        # Clothing coupons
        self.coupons.extend([
            Coupon(
                id="CLOTHING001",
                name="30% Off All Clothing",
                description="Save 30% on all clothing items",
                discount_type="percentage",
                discount_value=30.0,
                applicable_categories=["clothing", "apparel", "fashion"],
                valid_until=today + timedelta(days=14),
                code="CLOTHES30",
                restrictions=["Valid on clothing only"]
            ),
            Coupon(
                id="CLOTHING002",
                name="$10 Off Shoes",
                description="Save $10 on any shoe purchase of $50 or more",
                discount_type="dollar_off",
                discount_value=10.0,
                minimum_purchase=50.0,
                applicable_items=["shoes", "sneakers", "boots", "sandals"],
                applicable_categories=["clothing", "footwear"],
                valid_until=today + timedelta(days=21),
                code="SHOES10"
            )
        ])
        
        # Toys & Games coupons
        self.coupons.extend([
            Coupon(
                id="TOYS001",
                name="20% Off All Toys",
                description="Save 20% on all toys and games",
                discount_type="percentage",
                discount_value=20.0,
                applicable_categories=["toys", "games", "children"],
                valid_until=today + timedelta(days=21),
                code="TOYS20",
                restrictions=["Valid on toys and games only"]
            ),
            Coupon(
                id="TOYS002",
                name="$5 Off Board Games",
                description="Save $5 on any board game purchase",
                discount_type="dollar_off",
                discount_value=5.0,
                applicable_items=["board game", "board games", "puzzle", "puzzles"],
                applicable_categories=["toys", "games"],
                valid_until=today + timedelta(days=14),
                code="GAMES5"
            )
        ])
        
        # Home & Furniture coupons
        self.coupons.extend([
            Coupon(
                id="HOME001",
                name="15% Off All Home Decor",
                description="Save 15% on home decor and furniture",
                discount_type="percentage",
                discount_value=15.0,
                applicable_categories=["home", "furniture", "decor"],
                valid_until=today + timedelta(days=30),
                code="HOME15",
                restrictions=["Valid on home items only"]
            ),
            Coupon(
                id="HOME002",
                name="$20 Off Furniture",
                description="Save $20 on any furniture purchase of $100 or more",
                discount_type="dollar_off",
                discount_value=20.0,
                minimum_purchase=100.0,
                applicable_items=["furniture", "chair", "table", "sofa", "bed"],
                applicable_categories=["home", "furniture"],
                valid_until=today + timedelta(days=45),
                code="FURNITURE20"
            )
        ])
        
        # Baby & Kids coupons
        self.coupons.extend([
            Coupon(
                id="BABY001",
                name="25% Off All Baby Products",
                description="Save 25% on diapers, formula, and baby care items",
                discount_type="percentage",
                discount_value=25.0,
                applicable_items=["diaper", "diapers", "formula", "baby food", "baby care"],
                applicable_categories=["baby", "kids", "infant"],
                valid_until=today + timedelta(days=14),
                code="BABY25"
            ),
            Coupon(
                id="BABY002",
                name="$5 Off Diapers",
                description="Save $5 on any diaper purchase",
                discount_type="dollar_off",
                discount_value=5.0,
                applicable_items=["diaper", "diapers"],
                applicable_categories=["baby", "diapers"],
                valid_until=today + timedelta(days=7),
                code="DIAPER5"
            )
        ])
        
        # Garden Center coupons
        self.coupons.extend([
            Coupon(
                id="GARDEN001",
                name="20% Off All Plants",
                description="Save 20% on all plants and flowers",
                discount_type="percentage",
                discount_value=20.0,
                applicable_items=["plant", "plants", "flower", "flowers", "garden"],
                applicable_categories=["garden", "plants", "flowers"],
                valid_until=today + timedelta(days=21),
                code="PLANTS20"
            ),
            Coupon(
                id="GARDEN002",
                name="$3 Off Garden Tools",
                description="Save $3 on any garden tool purchase",
                discount_type="dollar_off",
                discount_value=3.0,
                applicable_items=["garden tool", "garden tools", "shovel", "rake", "pruner"],
                applicable_categories=["garden", "tools"],
                valid_until=today + timedelta(days=14),
                code="GARDEN3"
            )
        ])
        
        # Automotive coupons
        self.coupons.extend([
            Coupon(
                id="AUTO001",
                name="15% Off All Auto Parts",
                description="Save 15% on all automotive parts and accessories",
                discount_type="percentage",
                discount_value=15.0,
                applicable_categories=["automotive", "auto parts", "car parts"],
                valid_until=today + timedelta(days=30),
                code="AUTO15",
                restrictions=["Valid on auto parts only"]
            ),
            Coupon(
                id="AUTO002",
                name="$5 Off Motor Oil",
                description="Save $5 on any motor oil purchase",
                discount_type="dollar_off",
                discount_value=5.0,
                applicable_items=["motor oil", "oil", "engine oil"],
                applicable_categories=["automotive", "motor oil"],
                valid_until=today + timedelta(days=21),
                code="OIL5"
            )
        ])
    
    def search_coupons(self, query: CouponQuery) -> List[Coupon]:
        """Search for applicable coupons based on the query"""
        today = datetime.now()
        applicable_coupons = []
        
        for coupon in self.coupons:
            # Check if coupon is still valid
            if coupon.valid_until and today > coupon.valid_until:
                continue
            if coupon.valid_from and today < coupon.valid_from:
                continue
            
            # Check if coupon applies to the query
            if self._coupon_applies_to_query(coupon, query):
                applicable_coupons.append(coupon)
        
        return applicable_coupons
    
    def _coupon_applies_to_query(self, coupon: Coupon, query: CouponQuery) -> bool:
        """Check if a coupon applies to the given query"""
        if query.query_type == "general":
            # General store coupons always apply
            return True
        
        if query.item:
            item_lower = query.item.lower()
            
            # Check specific items
            if coupon.applicable_items:
                for item in coupon.applicable_items:
                    if item.lower() in item_lower or item_lower in item.lower():
                        return True
            
            # Check categories
            if coupon.applicable_categories:
                for category in coupon.applicable_categories:
                    if category.lower() in item_lower:
                        return True
        
        if query.category and coupon.applicable_categories:
            category_lower = query.category.lower()
            for category in coupon.applicable_categories:
                if category.lower() in category_lower or category_lower in category.lower():
                    return True
        
        return False
    
    def format_coupon_response(self, coupons: List[Coupon], query: CouponQuery) -> str:
        """Format the coupon response for the user"""
        if not coupons:
            if query.item:
                return f"I don't see any current coupons available for {query.item}. However, we do have some general store coupons that might help you save on your overall purchase."
            else:
                return "I don't see any specific coupons for that item, but we do have several store-wide promotions available."
        
        # For general coupon queries (no specific item), ask for department instead of listing all
        if query.query_type == "general" and not query.item and not query.category:
            return "Yes, we have coupons available today. What department are you shopping in?"
        
        # For specific item/category queries, provide detailed response
        response_parts = []
        
        if query.item:
            response_parts.append(f"Great! I found {len(coupons)} coupon(s) that can help you save on {query.item}:")
        else:
            response_parts.append(f"I found {len(coupons)} applicable coupon(s):")
        
        for i, coupon in enumerate(coupons[:3], 1):  # Limit to top 3 coupons
            discount_desc = self._format_discount_description(coupon)
            response_parts.append(f"{i}. {coupon.name}: {discount_desc}")
            
            if coupon.minimum_purchase:
                response_parts.append(f"   Minimum purchase: {self._format_money(coupon.minimum_purchase)}")
            
            if coupon.code:
                response_parts.append(f"   Coupon code: {coupon.code}")
            
            if coupon.restrictions:
                response_parts.append(f"   Note: {coupon.restrictions[0]}")
        
        if len(coupons) > 3:
            response_parts.append(f"... and {len(coupons) - 3} more coupons available.")
        
        response_parts.append("You can use these coupons at checkout. Just mention the coupon code to the cashier or enter it online.")
        
        return " ".join(response_parts)
    
    def _format_discount_description(self, coupon: Coupon) -> str:
        """Format the discount description for a coupon"""
        if coupon.discount_type == "percentage":
            # Convert percentage to word format for better TTS
            percentage_word = self._number_to_words(coupon.discount_value)
            return f"Save {percentage_word} percent off"
        elif coupon.discount_type == "dollar_off":
            return f"Save {self._format_money(coupon.discount_value)} off"
        elif coupon.discount_type == "buy_one_get_one":
            # Convert percentage to word format for better TTS
            percentage_word = self._number_to_words(coupon.discount_value)
            return f"Buy one, get one {percentage_word} percent off"
        elif coupon.discount_type == "free_item":
            return "Buy one, get one free"
        else:
            return coupon.description
    
    def _number_to_words(self, num: float) -> str:
        """Convert numbers to words for better TTS pronunciation"""
        # Handle common percentages
        if num == 10:
            return "ten"
        elif num == 15:
            return "fifteen"
        elif num == 20:
            return "twenty"
        elif num == 25:
            return "twenty-five"
        elif num == 30:
            return "thirty"
        elif num == 35:
            return "thirty-five"
        elif num == 40:
            return "forty"
        elif num == 45:
            return "forty-five"
        elif num == 50:
            return "fifty"
        elif num == 60:
            return "sixty"
        elif num == 70:
            return "seventy"
        elif num == 80:
            return "eighty"
        elif num == 90:
            return "ninety"
        else:
            # For other numbers, just return the number as a string
            # TTS will handle it better than with the % symbol
            return str(int(num)) if num.is_integer() else str(num)

    def _format_money(self, value: float) -> str:
        """Format money amounts to avoid trailing .0 for whole dollars."""
        try:
            # Treat near-integers as integers to avoid $5.0
            if float(value).is_integer():
                return f"${int(value)}"
            # Keep two decimals for non-integers
            return f"${value:.2f}"
        except Exception:
            return f"${value}"

def handle_coupon_query(query_text: str) -> str:
    """Main function to handle coupon queries"""
    query_text_lower = query_text.lower()
    
    # Check if this is a coupon-related query
    coupon_keywords = [
        "coupon", "coupons", "discount", "discounts", "deal", "deals", "sale", "savings",
        "save", "off", "promotion", "promotions", "offer", "offers", "code", "codes"
    ]
    
    if not any(keyword in query_text_lower for keyword in coupon_keywords):
        return None  # Not a coupon query
    
    # Extract item/category from query
    item = None
    category = None
    
    # Common grocery categories to look for
    categories = {
        "cereal": ["cereal", "cereals", "breakfast cereal"],
        "milk": ["milk", "dairy", "dairy products"],
        "meat": ["meat", "beef", "chicken", "pork", "turkey", "ground beef"],
        "produce": ["produce", "fruits", "vegetables", "fresh produce"],
        "pasta": ["pasta", "noodles", "spaghetti"],
        "canned": ["canned", "canned goods", "canned vegetables"],
        "cleaning": ["cleaning", "cleaning products", "household"],
        "beauty": ["beauty", "personal care", "health", "beauty products"]
    }
    
    for cat, keywords in categories.items():
        if any(keyword in query_text_lower for keyword in keywords):
            category = cat
            break
    
    # Look for specific items
    items = [
        "cereal", "milk", "cheese", "yogurt", "beef", "chicken", "pork", "turkey",
        "pasta", "canned goods", "cleaning products", "beauty products", "produce"
    ]
    
    for item_name in items:
        if item_name in query_text_lower:
            item = item_name
            break
    
    # Create coupon query
    query = CouponQuery(
        item=item,
        category=category,
        query_type="item_specific" if item or category else "general"
    )
    
    # Search for coupons
    coupon_manager = CouponManager()
    applicable_coupons = coupon_manager.search_coupons(query)
    
    # Format response
    return coupon_manager.format_coupon_response(applicable_coupons, query)

# Test the system
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What coupons can I use on cereal today?",
        "Do you have any coupons for milk?",
        "Are there any deals on meat?",
        "What discounts do you have?",
        "Any coupons for cleaning products?",
        "Do you have any savings on produce?"
    ]
    
    for test_query in test_queries:
        print(f"\nQuery: {test_query}")
        result = handle_coupon_query(test_query)
        if result:
            print(f"Response: {result}")
        else:
            print("Not a coupon query")
