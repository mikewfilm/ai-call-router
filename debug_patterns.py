#!/usr/bin/env python3
"""
Debug script to test regex patterns
"""

import re

def test_patterns():
    """Test the regex patterns directly"""
    
    test_cases = [
        "baguettes do you have those",
        "bread do you have it", 
        "nails do you carry those",
        "apples can you help",
        "milk do you have that",
        "the cheese do you sell it",
        "pasta do you carry it",
    ]
    
    # Test patterns
    patterns = [
        r"\s+do you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
        r"\s+can you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
        r"\s+do you\s+(?:have|carry|sell)\s*$",
        r"\s+can you\s+(?:have|carry|sell)\s*$",
        r"\s+do you\s*$",
        r"\s+can you\s*$",
        r"\s+can you\s+help\s*$",
    ]
    
    print("Testing patterns:")
    print("=" * 50)
    
    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        result = test_input
        
        for i, pattern in enumerate(patterns):
            before = result
            result = re.sub(pattern, "", result)
            if before != result:
                print(f"  Pattern {i+1} matched: '{pattern}'")
                print(f"  Before: '{before}'")
                print(f"  After:  '{result}'")
        
        print(f"Final result: '{result}'")

if __name__ == "__main__":
    test_patterns()
