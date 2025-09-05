#!/usr/bin/env python3
"""
Test script to verify that address abbreviation expansion works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_address_abbreviations():
    """Test that address abbreviations are expanded correctly"""
    
    print("🧪 Testing Address Abbreviation Expansion...")
    print("=" * 60)
    
    # Import the function from app.py
    import app
    
    test_cases = [
        # Street abbreviations
        ("123 Main St", "123 Main Street"),
        ("456 Oak Ave", "456 Oak Avenue"),
        ("789 Pine Blvd", "789 Pine Boulevard"),
        ("321 Elm Dr", "321 Elm Drive"),
        ("654 Maple Ln", "654 Maple Lane"),
        ("987 Cedar Rd", "987 Cedar Road"),
        ("147 Birch Ct", "147 Birch Court"),
        ("258 Spruce Pl", "258 Spruce Place"),
        ("369 Willow Way", "369 Willow Way"),
        ("741 Aspen Cir", "741 Aspen Circle"),
        ("852 Poplar Hwy", "852 Poplar Highway"),
        ("963 Sycamore Pkwy", "963 Sycamore Parkway"),
        ("159 Magnolia Ter", "159 Magnolia Terrace"),
        ("753 Dogwood Sq", "753 Dogwood Square"),
        
        # With periods
        ("123 Main St.", "123 Main Street"),
        ("456 Oak Ave.", "456 Oak Avenue"),
        ("789 Pine Blvd.", "789 Pine Boulevard"),
        
        # Directional abbreviations
        ("123 Main St N", "123 Main Street North"),
        ("456 Oak Ave S", "456 Oak Avenue South"),
        ("789 Pine Blvd E", "789 Pine Boulevard East"),
        ("321 Elm Dr W", "321 Elm Drive West"),
        ("654 Maple Ln NE", "654 Maple Lane North East"),
        ("987 Cedar Rd NW", "987 Cedar Road North West"),
        ("147 Birch Ct SE", "147 Birch Court South East"),
        ("258 Spruce Pl SW", "258 Spruce Place South West"),
        
        # With periods
        ("123 Main St N.", "123 Main Street North"),
        ("456 Oak Ave NE.", "456 Oak Avenue North East"),
        
        # State abbreviations
        ("123 Main St, Portland, OR", "123 Main Street, Portland, Oregon"),
        ("456 Oak Ave, Seattle, WA", "456 Oak Avenue, Seattle, Washington"),
        ("789 Pine Blvd, San Francisco, CA", "789 Pine Boulevard, San Francisco, California"),
        ("321 Elm Dr, New York, NY", "321 Elm Drive, New York, New York"),
        ("654 Maple Ln, Austin, TX", "654 Maple Lane, Austin, Texas"),
        ("987 Cedar Rd, Miami, FL", "987 Cedar Road, Miami, Florida"),
        
        # Complex combinations
        ("123 Main St NE, Portland, OR 97212", "123 Main Street North East, Portland, Oregon 97212"),
        ("456 Oak Ave SW, Seattle, WA 98101", "456 Oak Avenue South West, Seattle, Washington 98101"),
        ("789 Pine Blvd N, San Francisco, CA 94102", "789 Pine Boulevard North, San Francisco, California 94102"),
        
        # Apartment/Suite numbers
        ("123 Main St Apt 4B", "123 Main Street Apartment 4B"),
        ("456 Oak Ave Ste 200", "456 Oak Avenue Suite 200"),
        ("789 Pine Blvd Unit 5", "789 Pine Boulevard Unit 5"),
        ("321 Elm Dr Fl 3", "321 Elm Drive Floor 3"),
        ("654 Maple Ln Rm 101", "654 Maple Lane Room 101"),
        
        # Edge cases - should not change
        ("123 Main Street", "123 Main Street"),  # Already expanded
        ("456 Oak Avenue", "456 Oak Avenue"),    # Already expanded
        ("789 Pine North East", "789 Pine North East"),  # Already expanded
        ("321 Elm Oregon", "321 Elm Oregon"),    # Already expanded
    ]
    
    print("Testing _format_address_for_speech function:")
    print("-" * 60)
    
    all_passed = True
    for test_input, expected_output in test_cases:
        result = app._format_address_for_speech(test_input)
        passed = result == expected_output
        all_passed = all_passed and passed
        
        print(f"Input: '{test_input}'")
        print(f"Result: '{result}'")
        print(f"Expected: '{expected_output}'")
        print(f"Match: {'✅' if passed else '❌'}")
        print("-" * 40)
    
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    test_address_abbreviations()
