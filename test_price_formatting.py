#!/usr/bin/env python3
"""
Test script for clear price formatting
"""

# Import the function from app.py
from app import _format_price_clearly

def format_price_clearly(price: float) -> str:
    """Format price as clear dollars and cents"""
    # Handle floating point precision issues by converting to cents first
    total_cents = round(price * 100)
    dollars = total_cents // 100
    cents = total_cents % 100
    
    if price >= 100:
        if cents == 0:
            return f"${dollars} dollars"
        else:
            return f"${dollars} dollars and {cents} cents"
    elif price >= 10:
        if cents == 0:
            return f"${dollars} dollars"
        else:
            return f"${dollars} dollars and {cents} cents"
    else:
        if dollars == 0:
            return f"{cents} cents"
        else:
            return f"{dollars} dollars and {cents} cents"

def test_price_formatting():
    """Test various price formatting scenarios"""
    
    print("🧪 Testing Clear Price Formatting")
    print("=" * 50)
    
    test_prices = [
        (0.99, "99 cents"),
        (1.50, "1 dollar and 50 cents"),
        (2.99, "2 dollars and 99 cents"),
        (5.00, "$5 dollars"),
        (12.99, "$12 dollars and 99 cents"),
        (25.50, "$25 dollars and 50 cents"),
        (99.99, "$99 dollars and 99 cents"),
        (100.00, "$100 dollars"),
        (150.50, "$150 dollars and 50 cents"),
        (299.99, "$299 dollars and 99 cents"),
        (613.00, "$613 dollars"),
        (999.99, "$999 dollars and 99 cents"),
        (1250.00, "$1250 dollars")
    ]
    
    for price, expected in test_prices:
        formatted = _format_price_clearly(price)
        print(f"${price:.2f} → {formatted}")
        
        # Test with item names
        item_name = "Test Item"
        response = f"Yes, {item_name} is currently {formatted}."
        print(f"  Response: {response}")
        print()

def test_vacuum_cleaner_scenario():
    """Test the specific vacuum cleaner scenario"""
    
    print("🧹 Testing Vacuum Cleaner Scenario")
    print("=" * 50)
    
    # Simulate different vacuum cleaner prices
    vacuum_prices = [89.99, 199.99, 299.00, 450.50, 613.00, 899.99]
    
    for price in vacuum_prices:
        formatted = _format_price_clearly(price)
        response = f"Yes, the vacuum cleaner is currently {formatted}."
        print(f"${price:.2f} → {response}")

if __name__ == "__main__":
    test_price_formatting()
    print("\n" + "=" * 50)
    test_vacuum_cleaner_scenario()
