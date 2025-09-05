#!/usr/bin/env python3
"""
Test script to verify that item extraction fix works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_item_extraction_fix():
    """Test that item extraction correctly removes trailing question phrases"""
    
    print("🧪 Testing Item Extraction Fix...")
    print("=" * 50)
    
    # Import the function from app.py
    import app
    
    test_cases = [
        # Test cases that should be cleaned
        ("i'm looking for baguettes, do you have those?", "baguettes"),
        ("do you carry horizon organic milk?", "horizon organic milk"),
        ("where can i find bread do you have it?", "bread"),
        ("i need nails do you carry those?", "nails"),
        ("looking for apples can you help?", "apples"),
        ("i want milk do you have that?", "milk"),
        ("where is the cheese do you sell it?", "cheese"),
        ("i'm trying to find pasta do you carry it?", "pasta"),
        
        # Test cases that should remain mostly intact (first confirmation context)
        ("do you carry horizon organic milk?", "do you carry horizon organic milk", "confirm"),
        ("i need a bag of nails", "i need a bag of nails", "confirm"),
        ("looking for bread", "looking for bread", "confirm"),
    ]
    
    print("Testing extract_product_for_confirm function:")
    print("-" * 40)
    
    for test_input, expected_output, *context in test_cases:
        context = context[0] if context else "dept_choice"
        result = app.extract_product_for_confirm(test_input, context)
        print(f"Input: '{test_input}'")
        print(f"Context: {context}")
        print(f"Result: '{result}'")
        print(f"Expected: '{expected_output}'")
        print(f"Match: {'✅' if result == expected_output else '❌'}")
        print("-" * 30)
    
    print("✅ Test Complete!")

if __name__ == "__main__":
    test_item_extraction_fix()
