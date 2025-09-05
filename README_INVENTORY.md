# Inventory System for AI Call Router

## Overview

The inventory system provides comprehensive inventory management capabilities for the AI Call Router, allowing it to answer customer queries about product availability, pricing, and location. It's designed to work with both simulated data and real inventory systems.

## Features

### 🛍️ **Inventory Queries**
- **Stock checks**: "Do you have Juanita's chips in stock?"
- **Price checks**: "How much is Airborne chewables?"
- **Location queries**: "Where is Tide Pods located?"
- **Quantity queries**: "How many Lindor truffles do you have?"

### 📊 **Inventory Management**
- **Search functionality**: Find items by name, brand, or description
- **Stock tracking**: Real-time quantity monitoring
- **Price management**: Current pricing information
- **Location tracking**: Aisle and shelf locations
- **Department organization**: Categorized by store departments

### 🔄 **Flexible Data Sources**
- **Simulated data**: Built-in realistic inventory for testing
- **JSON import/export**: Easy data migration
- **Database integration**: Ready for real inventory systems
- **Real-time updates**: Support for live inventory feeds

## Quick Start

### 1. Basic Usage

```python
from inventory_system import search_inventory, check_stock, get_price

# Search for an item
result = search_inventory("Juanita's Tortilla Chips")
if result.found:
    item = result.items[0]
    print(f"Found: {item.name}")
    print(f"Price: ${item.price}")
    print(f"Stock: {item.quantity}")
    print(f"Location: {item.department}, aisle {item.aisle}")
```

### 2. Stock Checks

```python
from inventory_system import check_stock

# Check if item is in stock
in_stock, quantity = check_stock("GROC001")
if in_stock:
    print(f"In stock: {quantity} available")
else:
    print("Out of stock")
```

### 3. Price Queries

```python
from inventory_system import get_price

# Get item price
price = get_price("PHARM001")
if price:
    print(f"Price: ${price:.2f}")
```

## Integration with AI Call Router

The inventory system is automatically integrated into the AI Call Router. When customers ask inventory-related questions, the system will:

1. **Detect inventory queries** using keyword matching
2. **Search the inventory** for matching items
3. **Provide detailed responses** with stock, price, and location info
4. **Route to appropriate departments** when needed

### Example Customer Interactions

**Customer**: "Do you have Juanita's chips in stock?"
**AI**: "Juanita's Tortilla Chips is in stock - 45 available. It's located in Grocery, aisle A1, shelf S1."

**Customer**: "How much is Airborne chewables?"
**AI**: "Airborne Chewables is $8.99. It's located in Pharmacy, aisle F1."

**Customer**: "Where is Tide Pods located?"
**AI**: "Tide Pods Spring Meadow is located in Household, aisle D1, shelf S1."

## Data Structure

### InventoryItem
```python
@dataclass
class InventoryItem:
    sku: str                    # Unique product identifier
    name: str                   # Product name
    department: str             # Store department
    aisle: str                  # Aisle location
    shelf: str                  # Shelf location
    price: float                # Current price
    quantity: int               # Current stock quantity
    min_quantity: int = 0       # Minimum stock level
    max_quantity: int = 100     # Maximum stock level
    unit: str = "each"          # Unit of measurement
    brand: str = ""             # Product brand
    description: str = ""       # Product description
    last_updated: str = ""      # Last update timestamp
    is_active: bool = True      # Active status
```

### Search Results
```python
@dataclass
class InventorySearchResult:
    found: bool                 # Whether items were found
    items: List[InventoryItem]  # List of matching items
    total_count: int            # Number of matches
    search_term: str            # Original search term
    suggestions: List[str]      # Search suggestions if no match
```

## Configuration

### Environment Variables

The inventory system can be configured using environment variables:

```bash
# Data source configuration
INVENTORY_DATA_SOURCE=simulated  # simulated, json, database

# Inventory file paths
INVENTORY_JSON_FILE=inventory.json
INVENTORY_EXPORT_FILE=inventory_export.json

# Database configuration (for future use)
INVENTORY_DB_HOST=localhost
INVENTORY_DB_PORT=5432
INVENTORY_DB_NAME=inventory
INVENTORY_DB_USER=user
INVENTORY_DB_PASSWORD=password
```

### Data Sources

#### 1. Simulated Data (Default)
- Built-in realistic inventory data
- Perfect for testing and demos
- No external dependencies

#### 2. JSON Files
```python
# Export current inventory
inventory_manager.export_to_json("my_inventory.json")

# Import inventory from file
inventory_manager.import_from_json("my_inventory.json")
```

#### 3. Database Integration (Future)
- PostgreSQL, MySQL, SQLite support
- Real-time inventory updates
- Multi-store inventory management

## API Reference

### Core Functions

#### `search_inventory(search_term: str) -> InventorySearchResult`
Search for items by name, brand, or description.

#### `get_item_by_sku(sku: str) -> Optional[InventoryItem]`
Get item details by SKU.

#### `check_stock(sku: str) -> Tuple[bool, int]`
Check if item is in stock and return quantity.

#### `get_price(sku: str) -> Optional[float]`
Get current price for an item.

#### `get_department_summary(department: str) -> Dict[str, Any]`
Get summary statistics for a department.

### Inventory Manager Methods

#### `update_quantity(sku: str, new_quantity: int) -> bool`
Update item quantity (for real inventory integration).

#### `get_low_stock_items(threshold: int = 10) -> List[InventoryItem]`
Get items with low stock levels.

#### `get_items_by_department(department: str) -> List[InventoryItem]`
Get all items in a specific department.

#### `get_aisle_location(department: str) -> List[str]`
Get aisle locations for a department.

## Testing

Run the test script to see the inventory system in action:

```bash
python test_inventory.py
```

This will demonstrate:
- Item searches
- Stock checks
- Price queries
- Location queries
- Department summaries
- AI response simulation

## Real Inventory Integration

To connect to a real inventory system:

### 1. Database Integration
```python
class DatabaseInventoryManager(InventoryManager):
    def __init__(self, db_connection):
        self.db = db_connection
        super().__init__(data_source="database")
    
    def _load_database_data(self):
        # Load inventory from database
        query = "SELECT * FROM inventory_items WHERE active = true"
        results = self.db.execute(query)
        # Convert to InventoryItem objects
        # ...
```

### 2. API Integration
```python
class APIInventoryManager(InventoryManager):
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        super().__init__(data_source="api")
    
    def _load_api_data(self):
        # Load inventory from API
        response = requests.get(f"{self.api_url}/inventory", 
                              headers={"Authorization": f"Bearer {self.api_key}"})
        # Convert to InventoryItem objects
        # ...
```

### 3. File-based Integration
```python
# Load from CSV
import pandas as pd

def load_from_csv(filename: str):
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        item = InventoryItem(
            sku=row['sku'],
            name=row['name'],
            department=row['department'],
            # ... other fields
        )
        inventory_manager.inventory[item.sku] = item
```

## Future Enhancements

### Planned Features
- **Real-time updates**: WebSocket integration for live inventory
- **Multi-store support**: Chain-wide inventory management
- **Barcode scanning**: Integration with POS systems
- **Predictive analytics**: Stock level predictions
- **Vendor integration**: Automatic reorder notifications
- **Mobile app support**: Inventory management on mobile devices

### Performance Optimizations
- **Caching**: Redis integration for fast lookups
- **Indexing**: Advanced search indexing
- **Compression**: Efficient data storage
- **Load balancing**: Distributed inventory systems

## Troubleshooting

### Common Issues

#### 1. "Inventory system not found"
- Ensure `inventory_system.py` is in the same directory as `app.py`
- Check that all required dependencies are installed

#### 2. "Item not found" responses
- Verify the item exists in the inventory data
- Check spelling and try alternative search terms
- Use the search suggestions provided

#### 3. "Price not available"
- Ensure price data is loaded correctly
- Check the inventory data source configuration

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed inventory operations
```

## Support

For questions or issues with the inventory system:

1. Check the test script for examples
2. Review the API documentation
3. Test with simulated data first
4. Verify data source configuration

The inventory system is designed to be robust and easy to integrate, providing a solid foundation for both testing and production use.
