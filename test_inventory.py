#!/usr/bin/env python3
"""
Test script for the inventory system
Demonstrates inventory queries and responses
"""

from inventory_system import (
    search_inventory,
    get_item_by_sku,
    check_stock,
    get_price,
    get_department_summary,
    inventory_manager
)

def test_inventory_queries():
    """Test various inventory queries"""
    
    print("🧪 Testing Inventory System")
    print("=" * 50)
    
    # Test 1: Search for items
    print("\n1. Testing item search:")
    test_items = [
        "Juanita's Tortilla Chips",
        "Airborne Chewables", 
        "Tide Pods Spring Meadow",
        "Great Stuff Gaps and Cracks",
        "Dove Body Wash"
    ]
    
    for item in test_items:
        result = search_inventory(item)
        if result.found:
            item_obj = result.items[0]
            in_stock, qty = check_stock(item_obj.sku)
            price = get_price(item_obj.sku)
            print(f"✅ {item}: ${price:.2f}, {qty} in stock, {item_obj.department}")
        else:
            print(f"❌ {item}: Not found")
    
    # Test 2: Stock checks
    print("\n2. Testing stock checks:")
    stock_queries = [
        "Do you have Juanita's chips in stock?",
        "How many Airborne chewables do you have?",
        "Is Tide Pods available?",
        "Do you carry Great Stuff foam?"
    ]
    
    for query in stock_queries:
        print(f"Query: {query}")
        # This would be handled by the _handle_inventory_query function
        result = search_inventory(query)
        if result.found:
            item = result.items[0]
            in_stock, qty = check_stock(item.sku)
            if in_stock:
                if qty <= 5:
                    status = f"limited stock - only {qty} left"
                elif qty <= 20:
                    status = f"in stock - {qty} available"
                else:
                    status = "in stock"
                print(f"  ✅ {item.name}: {status}")
            else:
                print(f"  ❌ {item.name}: out of stock")
        else:
            print(f"  ❓ Item not found in query")
    
    # Test 3: Price checks
    print("\n3. Testing price checks:")
    price_queries = [
        "How much is Airborne chewables?",
        "What's the price of Tide Pods?",
        "How much does Great Stuff cost?"
    ]
    
    for query in price_queries:
        print(f"Query: {query}")
        result = search_inventory(query)
        if result.found:
            item = result.items[0]
            price = get_price(item.sku)
            print(f"  💰 {item.name}: ${price:.2f}")
        else:
            print(f"  ❓ Item not found in query")
    
    # Test 4: Location queries
    print("\n4. Testing location queries:")
    location_queries = [
        "Where is Juanita's chips?",
        "What aisle is Airborne in?",
        "Where can I find Tide Pods?"
    ]
    
    for query in location_queries:
        print(f"Query: {query}")
        result = search_inventory(query)
        if result.found:
            item = result.items[0]
            print(f"  📍 {item.name}: {item.department}, aisle {item.aisle}, shelf {item.shelf}")
        else:
            print(f"  ❓ Item not found in query")
    
    # Test 5: Department summaries
    print("\n5. Testing department summaries:")
    departments = ["Grocery", "Pharmacy", "Household", "Hardware"]
    
    for dept in departments:
        summary = get_department_summary(dept)
        if summary:
            print(f"📊 {dept}:")
            print(f"   Total items: {summary['total_items']}")
            print(f"   Total value: ${summary['total_value']:.2f}")
            print(f"   Low stock: {summary['low_stock_items']}")
            print(f"   Out of stock: {summary['out_of_stock_items']}")
            print(f"   Aisles: {', '.join(summary['aisles'])}")
    
    # Test 6: Low stock items
    print("\n6. Testing low stock items:")
    low_stock = inventory_manager.get_low_stock_items(threshold=10)
    for item in low_stock:
        print(f"⚠️  {item.name}: {item.quantity} left (${item.price:.2f})")
    
    print("\n" + "=" * 50)
    print("✅ Inventory system test complete!")

def test_inventory_response_simulation():
    """Simulate how the AI would respond to inventory queries"""
    
    print("\n🤖 Simulating AI Inventory Responses")
    print("=" * 50)
    
    # Simulate the _handle_inventory_query function
    def simulate_inventory_response(query: str) -> str:
        query_lower = query.lower()
        
        # Check for inventory keywords
        inventory_keywords = [
            "in stock", "out of stock", "have", "carry", "sell", "available",
            "price", "cost", "how much", "how many", "quantity", "amount",
            "where is", "location", "aisle", "shelf", "find", "locate"
        ]
        
        is_inventory_query = any(keyword in query_lower for keyword in inventory_keywords)
        if not is_inventory_query:
            return None
        
        # Search inventory
        result = search_inventory(query)
        if not result or not result.found:
            suggestions = result.suggestions if result else []
            if suggestions:
                return f"I'm sorry, I couldn't find that in our inventory. Did you mean {suggestions[0]}? Let me connect you to Customer Service."
            else:
                return "I'm sorry, I couldn't find that in our inventory. Let me connect you to Customer Service."
        
        # Item found
        item = result.items[0]
        in_stock, quantity = check_stock(item.sku)
        price = get_price(item.sku)
        
        # Build response based on query type
        if any(word in query_lower for word in ["price", "cost", "how much"]):
            return f"{item.name} is ${price:.2f}. It's located in {item.department}, aisle {item.aisle}."
        
        elif any(word in query_lower for word in ["in stock", "have", "carry", "available", "how many", "quantity"]):
            if in_stock:
                if quantity <= 5:
                    return f"{item.name} has limited stock - only {quantity} left. It's located in {item.department}, aisle {item.aisle}, shelf {item.shelf}."
                elif quantity <= 20:
                    return f"{item.name} is in stock - {quantity} available. It's located in {item.department}, aisle {item.aisle}, shelf {item.shelf}."
                else:
                    return f"{item.name} is in stock. It's located in {item.department}, aisle {item.aisle}, shelf {item.shelf}."
            else:
                return f"I'm sorry, {item.name} is currently out of stock. Let me connect you to {item.department} to check when it will be available again."
        
        elif any(word in query_lower for word in ["where", "location", "aisle", "shelf", "find", "locate"]):
            return f"{item.name} is located in {item.department}, aisle {item.aisle}, shelf {item.shelf}."
        
        else:
            # General inventory info
            if in_stock:
                stock_info = f"in stock with {quantity} available" if quantity <= 20 else "in stock"
                return f"{item.name} is {stock_info}. It's ${price:.2f} and located in {item.department}, aisle {item.aisle}."
            else:
                return f"{item.name} is currently out of stock. It's normally ${price:.2f} and located in {item.department}, aisle {item.aisle}."
    
    # Test queries
    test_queries = [
        "Do you have Juanita's chips in stock?",
        "How much is Airborne chewables?",
        "Where is Tide Pods located?",
        "Do you carry Great Stuff foam?",
        "What's the price of Dove body wash?",
        "How many Lindor truffles do you have?",
        "Where can I find Dawn dish soap?",
        "Is Benadryl available?"
    ]
    
    for query in test_queries:
        print(f"\nCustomer: {query}")
        response = simulate_inventory_response(query)
        if response:
            print(f"AI: {response}")
        else:
            print("AI: (Would route to department instead)")
    
    print("\n" + "=" * 50)
    print("✅ AI response simulation complete!")

if __name__ == "__main__":
    test_inventory_queries()
    test_inventory_response_simulation()
