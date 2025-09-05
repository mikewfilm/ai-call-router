#!/usr/bin/env python3
"""
Test script for simulated inventory responses
"""

from inventory_system import generate_simulated_inventory_response

def test_simulated_responses():
    """Test various simulated inventory responses"""
    
    print("🧪 Testing Simulated Inventory Responses")
    print("=" * 50)
    
    # Test various grocery item queries
    test_queries = [
        "price check on dave's killer bread",
        "how much is organic milk",
        "do you have doritos in stock",
        "what's the price of honey nut cheerios",
        "how much does coca cola cost",
        "price check on organic bananas",
        "do you carry ground beef",
        "how much is greek yogurt",
        "price check on artisan bread",
        "how much does premium coffee cost"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            item_name, department, price, quantity = generate_simulated_inventory_response(query)
            print(f"  Item: {item_name}")
            print(f"  Department: {department}")
            print(f"  Price: ${price:.2f}")
            print(f"  Quantity: {quantity}")
            
            # Simulate different response styles
            import random
            response_variants = [
                f"Yes, {item_name} is currently ${price:.2f}.",
                f"{item_name} is ${price:.2f} right now.",
                f"The price for {item_name} is ${price:.2f}.",
                f"{item_name} is on sale for ${price:.2f}.",
                f"We have {item_name} for ${price:.2f}."
            ]
            
            if quantity <= 5:
                response_variants.extend([
                    f"{item_name} is ${price:.2f}, but we're running low on stock.",
                    f"{item_name} is ${price:.2f} - only a few left!"
                ])
            elif quantity <= 15:
                response_variants.extend([
                    f"{item_name} is ${price:.2f} and we have good stock.",
                    f"{item_name} is ${price:.2f} - plenty available."
                ])
            
            response = random.choice(response_variants)
            print(f"  AI Response: {response}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Simulated response test complete!")

if __name__ == "__main__":
    test_simulated_responses()
