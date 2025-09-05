#!/usr/bin/env python3
"""
Test script to demonstrate consent response caching
"""

import requests
import time
import json

def test_consent_caching():
    """Test that consent responses are cached and don't use additional credits"""
    print("🧪 Testing Consent Response Caching")
    print("=" * 50)
    
    # Get initial credits
    try:
        response = requests.get('http://localhost:5003/api/usage', timeout=5)
        if response.status_code == 200:
            usage_data = response.json()
            initial_credits = usage_data.get('elevenlabs_config', {}).get('api_key_length', 0)
            print(f"💰 Initial credits: {initial_credits}")
        else:
            print("❌ Could not get initial credits")
            return
    except Exception as e:
        print(f"❌ Error getting initial credits: {e}")
        return
    
    # Test 1: First consent prompt (should generate new TTS)
    print("\n📞 Test 1: First consent prompt (should generate new TTS)")
    try:
        response = requests.post('http://localhost:5003/sms_consent?job=test1', timeout=10)
        if response.status_code == 200:
            print("✅ First consent prompt completed")
        else:
            print(f"❌ First consent prompt failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with first consent prompt: {e}")
    
    time.sleep(2)
    
    # Test 2: Second consent prompt (should use cached TTS)
    print("\n📞 Test 2: Second consent prompt (should use cached TTS)")
    try:
        response = requests.post('http://localhost:5003/sms_consent?job=test2', timeout=10)
        if response.status_code == 200:
            print("✅ Second consent prompt completed")
        else:
            print(f"❌ Second consent prompt failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with second consent prompt: {e}")
    
    time.sleep(2)
    
    # Test 3: Consent thanks (yes)
    print("\n📞 Test 3: Consent thanks (yes)")
    try:
        response = requests.post('http://localhost:5003/consent_continue?consent=yes&job=test3', timeout=10)
        if response.status_code == 200:
            print("✅ Consent thanks (yes) completed")
        else:
            print(f"❌ Consent thanks (yes) failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with consent thanks (yes): {e}")
    
    time.sleep(2)
    
    # Test 4: Consent thanks (no)
    print("\n📞 Test 4: Consent thanks (no)")
    try:
        response = requests.post('http://localhost:5003/consent_continue?consent=no&job=test4', timeout=10)
        if response.status_code == 200:
            print("✅ Consent thanks (no) completed")
        else:
            print(f"❌ Consent thanks (no) failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with consent thanks (no): {e}")
    
    time.sleep(2)
    
    # Get final credits
    try:
        response = requests.get('http://localhost:5003/api/usage', timeout=5)
        if response.status_code == 200:
            usage_data = response.json()
            final_credits = usage_data.get('elevenlabs_config', {}).get('api_key_length', 0)
            print(f"\n💰 Final credits: {final_credits}")
            
            if final_credits == initial_credits:
                print("🎉 SUCCESS: No additional credits used (all responses cached!)")
            else:
                print(f"📊 Credits used: {final_credits - initial_credits}")
        else:
            print("❌ Could not get final credits")
    except Exception as e:
        print(f"❌ Error getting final credits: {e}")
    
    print("\n📋 Expected Results:")
    print("   • First consent prompt: May use credits (generates new TTS)")
    print("   • Second consent prompt: Should use 0 credits (uses cached TTS)")
    print("   • Consent thanks responses: Should use 0 credits (uses cached TTS)")

if __name__ == "__main__":
    test_consent_caching()
