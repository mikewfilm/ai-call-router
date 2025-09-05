#!/usr/bin/env python3
"""
Test script to verify the confirmation fix works correctly
"""

def test_confirmation_extraction():
    """Test that confirmation responses are handled correctly"""
    
    print("🧪 Testing Confirmation Extraction Fix...")
    print("=" * 50)
    
    # Import the function after the fix
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the function from app.py
    import app
    
    test_cases = [
        ("That's right, buddy", "Should return None (affirmation + casual address)"),
        ("That's right", "Should return None (pure affirmation)"),
        ("Yes, that's correct", "Should return None (affirmation)"),
        ("No, I meant nails", "Should return 'nails' (correction)"),
        ("Actually, I need screws", "Should return 'screws' (correction)"),
        ("I said bag of nails", "Should return 'bag nails' (correction)"),
        ("buddy", "Should return None (casual address term)"),
        ("pal", "Should return None (casual address term)"),
        ("dude", "Should return None (casual address term)"),
    ]
    
    for test_input, expected_behavior in test_cases:
        result = app.extract_item_phrase(test_input)
        print(f"Input: '{test_input}'")
        print(f"Result: {result}")
        print(f"Expected: {expected_behavior}")
        print("-" * 30)
    
    print("✅ Test Complete!")

if __name__ == "__main__":
    test_confirmation_extraction()
