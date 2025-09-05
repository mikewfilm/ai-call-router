#!/usr/bin/env python3
"""
Test script to verify follow-up response detection is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_followup_response_detection():
    """Test that follow-up response detection works correctly"""
    
    print("🧪 Testing Follow-up Response Detection...")
    print("=" * 50)
    
    # Import the function from app.py
    import app
    
    test_cases = [
        # Negative responses (should return True - treat as "no")
        ("no", True, "Simple no"),
        ("nope", True, "Simple nope"),
        ("that's all", True, "That's all"),
        ("thanks", True, "Thanks"),
        ("goodbye", True, "Goodbye"),
        
        # Positive responses (should return False - treat as "yes")
        ("yes", False, "Simple yes"),
        ("yeah", False, "Simple yeah"),
        ("sure", False, "Sure"),
        ("okay", False, "Okay"),
        
        # Questions (should return False - treat as new question)
        ("what time do you close", False, "Question about hours"),
        ("where can I find milk", False, "Question about location"),
        ("do you have bread", False, "Question about inventory"),
        
        # Positive + Question combinations (should return False)
        ("yeah actually can you tell me where I'd find a bag of nails", False, "Positive + question"),
        ("yes where is the bathroom", False, "Yes + question"),
        ("sure what time do you open", False, "Sure + question"),
        
        # Product requests (should return False - treat as new question)
        ("bag of nails", False, "Product request"),
        ("looking for milk", False, "Looking for product"),
        ("need bread", False, "Need product"),
        ("want to find paper towels", False, "Want to find product"),
        
        # Long responses without negative words (should return False)
        ("I was wondering if you carry organic vegetables", False, "Long question"),
        ("can you help me locate the pet food section", False, "Help request"),
    ]
    
    print("Testing _is_followup_response function:")
    print("-" * 40)
    
    all_passed = True
    for test_input, expected_result, description in test_cases:
        result = app._is_followup_response(test_input)
        status = "✅ PASS" if result == expected_result else "❌ FAIL"
        print(f"{status} | '{test_input}' -> {result} (expected {expected_result}) | {description}")
        if result != expected_result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All follow-up response tests passed!")
    else:
        print("❌ Some follow-up response tests failed!")
    
    print("\n📋 Next Steps:")
    print("1. Call the voice app and ask for something")
    print("2. When asked 'is there anything else you need help with today?'")
    print("3. Say 'yeah actually can you tell me where I'd find a bag of nails?'")
    print("4. It should now process your request instead of saying goodbye")
    
    return all_passed

if __name__ == "__main__":
    test_followup_response_detection()
