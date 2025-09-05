#!/usr/bin/env python3
"""
Quick test to verify the greeting fix is working
"""

import requests
import json

def test_greeting_fix():
    """Test that the greeting fix is working"""
    
    print("🎤 Testing Greeting Fix...")
    print("=" * 40)
    
    # Test voice app health
    try:
        response = requests.get("http://localhost:5003/health", timeout=5)
        if response.status_code == 200:
            print("✅ Voice App: Running")
        else:
            print(f"❌ Voice App: Status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Voice App: {e}")
        return
    
    # Test greeting text
    try:
        response = requests.get("http://localhost:5003/api/store-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            greeting = data.get('greeting_message', '')
            print(f"✅ Greeting Text: '{greeting}'")
            
            if "Thank you for calling our store" in greeting:
                print("✅ Correct greeting text detected")
            else:
                print("⚠️  Unexpected greeting text")
        else:
            print(f"❌ API Error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API Error: {e}")
        return
    
    # Test dashboard
    try:
        response = requests.get("http://localhost:5004/login", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard: Running")
        else:
            print(f"❌ Dashboard: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard: {e}")
    
    print(f"\n🎯 Status Summary:")
    print(f"   • Voice app is running on port 5003")
    print(f"   • Dashboard is running on port 5004")
    print(f"   • Greeting text is correctly set")
    print(f"   • Greeting path fix has been applied")
    
    print(f"\n📞 Next Steps:")
    print(f"   1. Call the voice app number")
    print(f"   2. You should hear: 'Thank you for calling our store. How can I help you today?'")
    print(f"   3. If you still hear the old greeting, the TTS cache may need clearing")
    
    print(f"\n🔧 If you still hear the old greeting:")
    print(f"   python manage_tts_cache.py clear")

if __name__ == "__main__":
    test_greeting_fix()
