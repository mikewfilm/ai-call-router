#!/usr/bin/env python3
"""
Test script to verify single word fixes work correctly
"""

def test_single_word_extraction():
    """Test that single words are handled correctly"""
    
    print("🧪 Testing Single Word Extraction Fix...")
    print("=" * 50)
    
    # Import the function after the fix
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the function from app.py
    import app
    
    test_cases = [
        ("is", "Should return None (single word)"),
        ("are", "Should return None (single word)"),
        ("was", "Should return None (single word)"),
        ("yes", "Should return None (single word)"),
        ("no", "Should return None (single word)"),
        ("ok", "Should return None (single word)"),
        ("nails", "Should return 'nails' (valid product)"),
        ("bag of nails", "Should return 'bag nails' (valid product)"),
    ]
    
    for test_input, expected_behavior in test_cases:
        result = app.extract_item_phrase(test_input)
        print(f"Input: '{test_input}'")
        print(f"Result: {result}")
        print(f"Expected: {expected_behavior}")
        print("-" * 30)
    
    print("✅ Test Complete!")

if __name__ == "__main__":
    test_single_word_extraction()
