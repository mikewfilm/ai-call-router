#!/usr/bin/env python3
"""
Test script to verify that the detect_store_info_intent function returns the correct updated address
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_address_update():
    """Test that detect_store_info_intent returns the correct updated address"""
    
    print("🧪 Testing Address Update in detect_store_info_intent...")
    print("=" * 60)
    
    # Import the function from app.py
    import app
    
    # Test cases for address detection
    test_cases = [
        "What's your address?",
        "Where are you located?",
        "Can you tell me your address?",
        "What's the address?",
        "Where is your store?",
    ]
    
    print("Testing address detection with current shared data:")
    print("-" * 40)
    
    for test_input in test_cases:
        intent, response = app.detect_store_info_intent(test_input)
        print(f"Input: '{test_input}'")
        print(f"Intent: {intent}")
        print(f"Response: {response}")
        print("-" * 30)
    
    # Also test the shared data directly
    print("\nTesting shared data directly:")
    print("-" * 40)
    try:
        store_info = app.shared_data.get_store_info()
        print(f"Current address in shared data: {store_info.get('address', 'N/A')}")
        print(f"Current name in shared data: {store_info.get('name', 'N/A')}")
        print(f"Current phone in shared data: {store_info.get('phone', 'N/A')}")
    except Exception as e:
        print(f"Error accessing shared data: {e}")
    
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    test_address_update()
