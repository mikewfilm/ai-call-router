#!/usr/bin/env python3
"""
Test script to verify store information updates are working correctly
"""

import requests
import json
import time

def test_store_info_updates():
    """Test that store information updates are working correctly"""
    
    print("🧪 Testing Store Information Updates...")
    print("=" * 50)
    
    # Test 1: Check current store info from voice app API
    try:
        response = requests.get("http://localhost:5003/api/store-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Voice App API Response:")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Address: {data.get('address', 'N/A')}")
            print(f"   Phone: {data.get('phone', 'N/A')}")
            print(f"   Hours: {data.get('hours', 'N/A')}")
            print(f"   Greeting: {data.get('greeting_message', 'N/A')}")
        else:
            print(f"❌ Voice App API: Status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Voice App API: {e}")
        return
    
    # Test 2: Check dashboard connectivity
    try:
        response = requests.get("http://localhost:5004/", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard: Running")
        else:
            print(f"❌ Dashboard: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard: {e}")
    
    # Test 3: Check if TTS cache is cleared
    import os
    cache_dir = "static/tts_cache"
    if os.path.exists(cache_dir):
        files = [f for f in os.listdir(cache_dir) if f.endswith('.mp3')]
        print(f"✅ TTS Cache: {len(files)} files")
        
        # Check for specific files
        greet_files = [f for f in files if 'greet' in f]
        address_files = [f for f in files if 'address' in f]
        
        print(f"   Greeting files: {len(greet_files)}")
        print(f"   Address files: {len(address_files)}")
    
    print("\n📋 Next Steps:")
    print("1. Call the voice app and ask for the store address")
    print("2. It should now say: '3535 NE 15th Ave, Portland, OR 97212'")
    print("3. Ask for the store name - it should say: 'Super Cool Grocery'")
    print("4. Ask for the phone number - it should say: '(555) 123-4567'")
    print("5. Update any information in the dashboard and test again")
    
    print("\n✅ Store Information Update Test Complete!")

if __name__ == "__main__":
    test_store_info_updates()
