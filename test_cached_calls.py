#!/usr/bin/env python3
"""
Test script for making calls that use mostly cached content
to demonstrate credit savings.
"""

import requests
import time
import json

def make_test_call(scenario_name, speech_input, expected_credits=0):
    """Make a test call and check credit usage"""
    print(f"\n🧪 Testing: {scenario_name}")
    print(f"📝 Input: '{speech_input}'")
    
    # Get credits before call
    try:
        response = requests.get('http://localhost:5003/api/usage', timeout=5)
        if response.status_code == 200:
            usage_data = response.json()
            credits_before = usage_data.get('elevenlabs_config', {}).get('api_key_length', 0)
        else:
            credits_before = "Unknown"
    except:
        credits_before = "Unknown"
    
    print(f"💰 Credits before: {credits_before}")
    
    # Make the call
    call_data = {
        "SpeechResult": speech_input,
        "Confidence": "0.9",
        "CallSid": f"test_{scenario_name}_{int(time.time())}"
    }
    
    try:
        response = requests.post('http://localhost:5003/voice', data=call_data, timeout=10)
        if response.status_code == 200:
            print("✅ Call completed successfully")
        else:
            print(f"❌ Call failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Call error: {e}")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Get credits after call
    try:
        response = requests.get('http://localhost:5003/api/usage', timeout=5)
        if response.status_code == 200:
            usage_data = response.json()
            credits_after = usage_data.get('elevenlabs_config', {}).get('api_key_length', 0)
        else:
            credits_after = "Unknown"
    except:
        credits_after = "Unknown"
    
    print(f"💰 Credits after: {credits_after}")
    
    if credits_before != "Unknown" and credits_after != "Unknown":
        if credits_before == credits_after:
            print("🎉 SUCCESS: No new credits used (all cached!)")
        else:
            print(f"📊 Credits used: {credits_after - credits_before}")
    else:
        print("⚠️  Could not determine credit usage")

def main():
    print("🎯 Testing Cached Call Scenarios")
    print("=" * 50)
    
    # Test scenarios that should use mostly cached content
    test_scenarios = [
        {
            "name": "Basic Greeting Only",
            "input": "hello",
            "description": "Should use cached greeting only"
        },
        {
            "name": "Department Connection",
            "input": "I need to talk to someone in grocery",
            "description": "Should use cached greeting + cached department connection"
        },
        {
            "name": "Pharmacy Inquiry",
            "input": "I need to check on my prescription",
            "description": "Should use cached greeting + cached pharmacy response"
        },
        {
            "name": "Coupon Request",
            "input": "Do you have any coupons?",
            "description": "Should use cached greeting + cached coupon response"
        },
        {
            "name": "Error Handling (Silence)",
            "input": "",
            "description": "Should use cached greeting + cached error message"
        }
    ]
    
    for scenario in test_scenarios:
        make_test_call(scenario["name"], scenario["input"])
        print(f"📋 {scenario['description']}")
        print("-" * 50)
        time.sleep(3)  # Wait between calls
    
    print("\n🎉 All tests completed!")
    print("\n💡 Expected Results:")
    print("   • Most calls should use 0 new credits")
    print("   • Only truly unique responses will use credits")
    print("   • Cached content includes: greetings, department connections, error messages")

if __name__ == "__main__":
    main()
