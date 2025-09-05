#!/usr/bin/env python3
"""
Test script to verify dashboard and voice app integration
"""

import requests
import json
import time

def test_voice_app_api():
    """Test the voice app API endpoints"""
    base_url = "http://localhost:5003"
    
    print("🧪 Testing Voice App API Integration...")
    
    # Test 1: Get store info
    print("\n1. Testing GET /api/store-info...")
    try:
        response = requests.get(f"{base_url}/api/store-info", timeout=5)
        if response.status_code == 200:
            store_info = response.json()
            print(f"✅ Store info retrieved: {store_info.get('name', 'Unknown')}")
            print(f"   Address: {store_info.get('address', 'Unknown')}")
            print(f"   Greeting: {store_info.get('greeting_message', 'Unknown')}")
        else:
            print(f"❌ Failed to get store info: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting store info: {e}")
    
    # Test 2: Update store info
    print("\n2. Testing PUT /api/store-info...")
    try:
        updated_info = {
            "name": "Test Store Updated",
            "address": "456 Test Street, Test City, TS 12345",
            "phone": "(555) 999-8888",
            "hours": "Mon-Fri 9AM-10PM, Sat-Sun 10AM-8PM",
            "greeting_message": "Thank you for calling Test Store. How may I assist you today?"
        }
        
        response = requests.put(
            f"{base_url}/api/store-info",
            json=updated_info,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Store info updated successfully")
            
            # Verify the update
            response = requests.get(f"{base_url}/api/store-info", timeout=5)
            if response.status_code == 200:
                store_info = response.json()
                if store_info.get('name') == "Test Store Updated":
                    print("✅ Update verified - store name changed")
                else:
                    print("❌ Update not verified - store name unchanged")
        else:
            print(f"❌ Failed to update store info: {response.status_code}")
    except Exception as e:
        print(f"❌ Error updating store info: {e}")
    
    # Test 3: Get departments
    print("\n3. Testing GET /api/departments...")
    try:
        response = requests.get(f"{base_url}/api/departments", timeout=5)
        if response.status_code == 200:
            departments = response.json()
            print(f"✅ Retrieved {len(departments)} departments")
            for dept in departments[:3]:  # Show first 3
                print(f"   - {dept.get('name', 'Unknown')} (ext: {dept.get('phone_extension', 'Unknown')})")
        else:
            print(f"❌ Failed to get departments: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting departments: {e}")
    
    # Test 4: Add a department
    print("\n4. Testing POST /api/departments...")
    try:
        new_dept = {
            "name": "Test Department",
            "phone_extension": "999",
            "description": "A test department for integration testing",
            "is_active": True
        }
        
        response = requests.post(
            f"{base_url}/api/departments",
            json=new_dept,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Department added successfully")
        else:
            print(f"❌ Failed to add department: {response.status_code}")
    except Exception as e:
        print(f"❌ Error adding department: {e}")
    
    # Test 5: Get inventory
    print("\n5. Testing GET /api/inventory...")
    try:
        response = requests.get(f"{base_url}/api/inventory", timeout=5)
        if response.status_code == 200:
            inventory = response.json()
            print(f"✅ Retrieved {len(inventory)} inventory items")
            for item in inventory[:3]:  # Show first 3
                print(f"   - {item.get('name', 'Unknown')} (${item.get('price', 0)})")
        else:
            print(f"❌ Failed to get inventory: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting inventory: {e}")

def test_dashboard_integration():
    """Test the dashboard integration"""
    print("\n🧪 Testing Dashboard Integration...")
    
    # Test 1: Check if dashboard is running
    print("\n1. Testing dashboard connectivity...")
    try:
        response = requests.get("http://localhost:5004", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard is running")
        else:
            print(f"❌ Dashboard returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard not accessible: {e}")

def main():
    print("🚀 Starting Integration Tests...")
    print("=" * 50)
    
    # Test voice app API
    test_voice_app_api()
    
    # Test dashboard integration
    test_dashboard_integration()
    
    print("\n" + "=" * 50)
    print("🏁 Integration Tests Complete!")
    print("\n📋 Next Steps:")
    print("1. Start the voice app: ./start_app.sh")
    print("2. Start the dashboard: ./start_dashboard_simple.sh")
    print("3. Make changes in the dashboard")
    print("4. Test that changes appear in voice app responses")

if __name__ == "__main__":
    main()
