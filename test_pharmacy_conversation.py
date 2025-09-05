#!/usr/bin/env python3
"""
Test script for improved pharmacy conversation flow
"""

from app import _handle_pharmacy_query

def test_pharmacy_conversation_flow():
    """Test the improved pharmacy conversation flow"""
    
    print("💊 Testing Improved Pharmacy Conversation Flow")
    print("=" * 60)
    
    # Simulate a conversation
    conversation_steps = [
        "I need to refill my prescription",
        "My phone number is 555-123-4567",
        "refill prescription for 555-123-4567",
        "Is my prescription ready?",
        "Check status for 555-123-4567",
        "What are your pharmacy hours?",
        "I want to transfer from CVS",
        "I need to speak to a pharmacist"
    ]
    
    for i, query in enumerate(conversation_steps, 1):
        print(f"\n{i}. Customer: {query}")
        result = _handle_pharmacy_query(query)
        if result:
            response, department = result
            print(f"   AI: {response}")
            print(f"   Department: {department}")
        else:
            print("   AI: (Would route to department instead)")
    
    print("\n" + "=" * 60)
    print("✅ Conversation flow test complete!")

def test_specific_scenarios():
    """Test specific scenarios that were problematic before"""
    
    print("\n🎯 Testing Specific Scenarios")
    print("=" * 60)
    
    scenarios = [
        ("Initial refill request", "I need to refill my prescription"),
        ("Follow-up with phone", "refill prescription for 555-123-4567"),
        ("Quick refill", "refill same as last time"),
        ("Status check", "Check status for 555-123-4567"),
        ("General question", "What are your pharmacy hours?"),
        ("Transfer request", "I want to transfer from CVS"),
        ("Consultation request", "I need to speak to a pharmacist")
    ]
    
    for scenario_name, query in scenarios:
        print(f"\n{scenario_name}:")
        print(f"  Customer: {query}")
        result = _handle_pharmacy_query(query)
        if result:
            response, department = result
            print(f"  AI: {response}")
            print(f"  Department: {department}")
            # Check if it would hang up (requires_staff=True) or continue conversation
            if "connect you to" in response and "staff" in response:
                print(f"  ⚠️  Would connect to staff (might hang up)")
            else:
                print(f"  ✅ Would continue conversation")
        else:
            print(f"  AI: (Would route to department instead)")

if __name__ == "__main__":
    test_pharmacy_conversation_flow()
    test_specific_scenarios()
